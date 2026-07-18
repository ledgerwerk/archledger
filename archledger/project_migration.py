from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from ledgercore.refs import parse_local_ref

from archledger.config.model import (
    Arc42ProfileConfig,
    ProjectConfig,
    ProjectProfilesConfig,
)
from archledger.config.parse import load_project_config
from archledger.config.render import render_project_config
from archledger.errors import ConfigError, StorageError
from archledger.ledgercore_backend import (
    initialize_archledger_bindings,
    parse_ledger_project_manifest,
)
from archledger.project_context import (
    ARCHLEDGER_CONFIG_PATH,
    classify_project_state,
    load_project_context,
)
from archledger.project_manifest import (
    ensure_archledger_registration,
    ensure_project_identity,
    load_manifest,
    manifest_text,
    new_manifest,
    write_manifest,
)
from archledger.storage.common import write_text_atomic
from archledger.storage.meta import read_storage_meta
from archledger.storage.source_state import read_source_state

MigrationSourceKind = Literal[
    "legacy-default",
    "legacy-hidden-config",
    "legacy-visible-config",
    "legacy-relative-data",
    "legacy-absolute-data",
    "canonical-config-legacy-shape",
    "canonical-data-unregistered",
    "canonical",
    "partial",
    "invalid",
]

_RECOGNIZED_TOP_LEVEL = {
    "storage.yaml",
    "source-state.json",
    "document-state.json",
    "profiles",
    "sections",
    "records",
    "archive",
    "migrations",
}


@dataclass(frozen=True, slots=True)
class MigrationIssue:
    severity: Literal["blocker", "warning", "info"]
    code: str
    message: str
    remediation: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MigrationCopyItem:
    source: Path | None
    destination: Path
    category: str
    action: str
    verification: str


@dataclass(frozen=True, slots=True)
class ArchledgerMigrationInspection:
    project_root: Path
    source_kind: MigrationSourceKind
    legacy_config_candidates: tuple[Path, ...]
    source_config_path: Path | None
    source_data_root: Path | None
    source_project_uuid: str | None
    canonical_project_uuid: str | None
    manifest_path: Path
    local_config_path: Path
    stable_config_path: Path
    target_data_root: Path
    target_migrations_dir: Path
    staging_root: Path
    backup_root: Path
    record_count: int
    section_count: int
    archived_record_count: int
    tombstone_count: int
    highest_number: int
    stored_next_number: int | None
    copy_items: tuple[MigrationCopyItem, ...]
    issues: tuple[MigrationIssue, ...]
    ready: bool
    migration_required: bool
    source_config_version: int | None = None
    uuid_evidence: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class ArchledgerMigrationResult:
    inspection: ArchledgerMigrationInspection
    backup_root: Path
    staging_root: Path
    receipt_path: Path
    copied: tuple[Path, ...]
    skipped: tuple[Path, ...]
    retired: tuple[Path, ...]


def _issue(code: str, message: str, *, blocker: bool = True) -> MigrationIssue:
    return MigrationIssue(
        severity="blocker" if blocker else "warning",
        code=code,
        message=message,
        remediation=("Review the migration report before applying.",),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_root(start: Path) -> Path:
    current = start.resolve(strict=False)
    if current.is_file():
        current = current.parent
    while True:
        if (current / ".ledger/ledger.toml").is_file():
            return current
        if (current / "archledger.toml").is_file() or (
            current / ".archledger.toml"
        ).is_file():
            return current
        if current.parent == current:
            return start.resolve(strict=False)
        current = current.parent


def _legacy_candidates(root: Path) -> tuple[Path, ...]:
    return tuple(
        path
        for path in (root / ".archledger.toml", root / "archledger.toml")
        if path.is_file()
    )


def _target_for_source(source_root: Path, source_path: Path, target_root: Path) -> Path:
    relative = source_path.relative_to(source_root)
    if relative.parts and relative.parts[0] == "sections":
        return target_root / "profiles/arc42/sections" / Path(*relative.parts[1:])
    return target_root / relative


def _inventory(data_root: Path) -> tuple[int, int, int, int, int]:
    record_count = (
        sum(1 for path in (data_root / "records").rglob("*") if path.is_file())
        if (data_root / "records").is_dir()
        else 0
    )
    section_roots = [data_root / "sections", data_root / "profiles/arc42/sections"]
    section_count = sum(
        1
        for root in section_roots
        if root.is_dir()
        for path in root.rglob("*")
        if path.is_file()
    )
    archived = data_root / "archive/records"
    archived_count = (
        sum(1 for path in archived.rglob("*") if path.is_file())
        if archived.is_dir()
        else 0
    )
    tombstones = data_root / "archive/tombstones"
    tombstone_count = (
        sum(1 for path in tombstones.rglob("*") if path.is_file())
        if tombstones.is_dir()
        else 0
    )
    highest = 0
    for path in data_root.rglob("*") if data_root.is_dir() else ():
        if not path.is_file():
            continue
        try:
            highest = max(highest, parse_local_ref(path.stem).number)
        except Exception:
            continue
    return record_count, section_count, archived_count, tombstone_count, highest


def _stable_config(source: ProjectConfig) -> ProjectConfig:
    profiles = source.profiles
    if not source.profiles_present or not profiles.arc42.sections_dir.startswith(
        "profiles/"
    ):
        profiles = ProjectProfilesConfig(
            profiles=profiles.profiles,
            arc42=Arc42ProfileConfig(
                kind=profiles.arc42.kind,
                template=profiles.arc42.template,
                sections_dir="profiles/arc42/sections",
                build_template=profiles.arc42.build_template,
                include_help=profiles.arc42.include_help,
            ),
        )
    return source.__class__(
        **{
            **{
                field.name: getattr(source, field.name)
                for field in source.__dataclass_fields__.values()
            },
            "config_version": 12,
            "archledger_dir": "",
            "project_uuid": "",
            "project_name": "",
            "build_output_dir": source.build_output_dir or ".",
            "tracking_exclude": tuple(
                dict.fromkeys((*source.tracking_exclude, ".ledger/**"))
            ),
            "profiles": profiles,
            "profiles_present": True,
        }
    )


def inspect_project_migration(  # noqa: C901
    start: Path,
    *,
    source_config: Path | None = None,
) -> ArchledgerMigrationInspection:
    root = _project_root(start)
    manifest_path = root / ".ledger/ledger.toml"
    local_config_path = root / ".ledger/ledger.local.toml"
    stable_config_path = root / ARCHLEDGER_CONFIG_PATH
    target_data_root = root / ".ledger/archledger/data"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = root / ".ledger/backups" / f"archledger-{timestamp}"
    staging_root = root / ".ledger/arch" / f".archledger-migration-{timestamp}"
    candidates = _legacy_candidates(root)
    issues: list[MigrationIssue] = []
    evidence: list[tuple[str, str]] = []
    source_path = (
        source_config.resolve()
        if source_config is not None
        else (candidates[0] if candidates else None)
    )
    source_root: Path | None = None
    source_data: Path | None = None
    source_cfg: ProjectConfig | None = None
    source_kind: MigrationSourceKind = "legacy-default"
    canonical_uuid: str | None = None

    if manifest_path.is_file():
        try:
            manifest = load_manifest(manifest_path)
            import sys

            if sys.version_info >= (3, 11):
                import tomllib
            else:
                import tomli as tomllib
            parsed = parse_ledger_project_manifest(
                tomllib.loads(manifest_text(manifest))
            )
            canonical_uuid = parsed.project_uuid
            evidence.append((str(manifest_path), parsed.project_uuid))
            target_data_root = root / ".ledger/archledger/data"
            staging_root = root / ".ledger/arch" / f".archledger-migration-{timestamp}"
        except Exception as exc:
            issues.append(
                _issue("STABLE_CONFIG_CONFLICT", f"Shared manifest is invalid: {exc}")
            )
    if (
        candidates
        and len(candidates) == 2
        and candidates[0].read_bytes() != candidates[1].read_bytes()
    ):
        issues.append(
            _issue(
                "LEGACY_CONFIG_CONFLICT", "Visible and hidden legacy configs differ."
            )
        )
    if source_path is not None and source_path.is_file():
        try:
            source_cfg = load_project_config(source_path)
            source_root = source_path.parent.resolve()
            source_value = source_cfg.archledger_dir
            source_data = (
                Path(source_value)
                if Path(source_value).is_absolute()
                else source_root / source_value
            ).resolve(strict=False)
            if source_cfg.project_uuid:
                evidence.append((str(source_path), source_cfg.project_uuid))
                target_data_root = root / ".ledger/archledger/data"
                staging_root = target_data_root.parent / (
                    f".archledger-migration-{timestamp}"
                )
            if source_cfg.config_version == 11:
                source_kind = "canonical-config-legacy-shape"
            elif Path(source_value).is_absolute():
                source_kind = "legacy-absolute-data"
            elif source_value == ".archledger":
                source_kind = (
                    "legacy-hidden-config"
                    if source_path.name.startswith(".")
                    else "legacy-default"
                )
            else:
                source_kind = "legacy-relative-data"
        except ConfigError as exc:
            issues.append(_issue("STABLE_CONFIG_CONFLICT", str(exc)))
            source_kind = "invalid"
    elif target_data_root.is_dir() or stable_config_path.is_file():
        source_kind = "partial"
    else:
        issues.append(
            _issue("SOURCE_DATA_MISSING", "No legacy Archledger config was found.")
        )
        source_kind = "invalid"

    if source_data is not None:
        if source_data.is_symlink():
            issues.append(
                _issue("SOURCE_SYMLINK", f"Legacy source is a symlink: {source_data}")
            )
        elif not source_data.exists():
            issues.append(
                _issue(
                    "SOURCE_DATA_MISSING", f"Legacy data root is missing: {source_data}"
                )
            )
        elif not source_data.is_dir():
            issues.append(
                _issue(
                    "SOURCE_DATA_NOT_DIRECTORY",
                    f"Legacy data root is not a directory: {source_data}",
                )
            )
        else:
            unknown = sorted(
                path.name
                for path in source_data.iterdir()
                if path.name not in _RECOGNIZED_TOP_LEVEL
            )
            for name in unknown:
                issues.append(
                    _issue("UNKNOWN_SOURCE_ENTRY", f"Unknown legacy data entry: {name}")
                )
            try:
                meta = read_storage_meta(source_data / "storage.yaml")
                evidence.append((str(source_data / "storage.yaml"), meta.project_uuid))
            except StorageError as exc:
                issues.append(_issue("STORAGE_META_INVALID", str(exc)))

    if source_cfg is not None and source_data is not None and source_data.is_dir():
        try:
            source_state = read_source_state(
                source_data / source_cfg.tracking_state_file
            )
            if source_state is not None and source_state.project_uuid:
                evidence.append(
                    (
                        str(source_data / source_cfg.tracking_state_file),
                        source_state.project_uuid,
                    )
                )
        except (OSError, StorageError):
            issues.append(
                _issue(
                    "SOURCE_STATE_UUID_MISMATCH",
                    "Legacy source-state.json could not be validated.",
                )
            )

    if len({value for _, value in evidence}) > 1:
        issues.append(
            _issue("PROJECT_UUID_MISMATCH", "Project UUID evidence does not agree.")
        )
    source_uuid = next(
        (value for path, value in evidence if path == str(source_path)), None
    )
    if canonical_uuid is None and source_uuid is not None:
        canonical_uuid = source_uuid

    if manifest_path.is_file() and source_kind in {
        "legacy-default",
        "legacy-hidden-config",
        "legacy-visible-config",
        "legacy-relative-data",
        "legacy-absolute-data",
    }:
        try:
            manifest = load_manifest(manifest_path)
            raw = manifest.get("ledgers", {})
            if isinstance(raw, dict) and raw.get("archledger") is not None:
                issues.append(
                    _issue(
                        "REGISTRATION_CONFLICT",
                        "Manifest already registers Archledger while "
                        "legacy data remains.",
                    )
                )
        except ConfigError:
            pass

    record_count = section_count = archived_count = tombstone_count = highest = 0
    stored_next: int | None = None
    if source_data is not None and source_data.is_dir():
        record_count, section_count, archived_count, tombstone_count, highest = (
            _inventory(source_data)
        )
        try:
            stored_next = read_storage_meta(source_data / "storage.yaml").next_number
            if stored_next <= highest:
                issues.append(
                    _issue(
                        "COUNTER_STALE",
                        "storage.yaml next_number is below the derived sequence floor.",
                        blocker=False,
                    )
                )
        except StorageError:
            pass

    copy_items: list[MigrationCopyItem] = []
    if source_data is not None and source_data.is_dir():
        for source_file in sorted(
            path for path in source_data.rglob("*") if path.is_file()
        ):
            destination = _target_for_source(source_data, source_file, target_data_root)
            action = (
                "copy"
                if not destination.exists()
                else "skip-identical"
                if _sha256(source_file) == _sha256(destination)
                else "block-conflict"
            )
            if action == "block-conflict":
                issues.append(
                    _issue(
                        "DESTINATION_CONFLICT", f"Destination differs: {destination}"
                    )
                )
            copy_items.append(
                MigrationCopyItem(
                    source_file, destination, "storage-state", action, "sha256"
                )
            )

    if source_cfg is not None and stable_config_path.exists():
        try:
            stable = load_project_config(stable_config_path)
            if stable.config_version != 11:
                issues.append(
                    _issue(
                        "STABLE_CONFIG_LEGACY_SHAPE",
                        "Canonical config is not version 11.",
                    )
                )
        except ConfigError as exc:
            issues.append(_issue("STABLE_CONFIG_CONFLICT", str(exc)))
    if source_cfg is not None:
        copy_items.append(
            MigrationCopyItem(
                source_path,
                stable_config_path,
                "stable-config",
                "rewrite",
                "toml-semantic",
            )
        )

    blockers = tuple(item for item in issues if item.severity == "blocker")
    canonical = classify_project_state(root) == "canonical"
    if canonical:
        source_kind = "canonical"
    return ArchledgerMigrationInspection(
        project_root=root,
        source_kind=source_kind,
        legacy_config_candidates=candidates,
        source_config_path=source_path,
        source_data_root=source_data,
        source_project_uuid=source_uuid,
        canonical_project_uuid=canonical_uuid,
        manifest_path=manifest_path,
        local_config_path=local_config_path,
        stable_config_path=stable_config_path,
        target_data_root=target_data_root,
        target_migrations_dir=target_data_root / "migrations",
        staging_root=staging_root,
        backup_root=backup_root,
        record_count=record_count,
        section_count=section_count,
        archived_record_count=archived_count,
        tombstone_count=tombstone_count,
        highest_number=highest,
        stored_next_number=stored_next,
        copy_items=tuple(copy_items),
        issues=tuple(issues),
        ready=not blockers,
        migration_required=not canonical,
        source_config_version=source_cfg.config_version if source_cfg else None,
        uuid_evidence=tuple(evidence),
    )


def _backup_path(source: Path, backup_root: Path, root: Path) -> Path:
    try:
        relative = source.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        relative = Path("external") / source.name
    return backup_root / relative


def _backup(inspection: ArchledgerMigrationInspection, backup_root: Path) -> None:
    backup_root.mkdir(parents=True, exist_ok=False)
    manifest: list[dict[str, object]] = []
    candidates = [
        *inspection.legacy_config_candidates,
        inspection.manifest_path,
        inspection.local_config_path,
        inspection.stable_config_path,
    ]
    if inspection.source_data_root is not None:
        candidates.append(inspection.source_data_root)
    for source in candidates:
        if not source.exists() and not source.is_symlink():
            continue
        destination = _backup_path(source, backup_root, inspection.project_root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            destination.write_text(os.readlink(source), encoding="utf-8")
            digest = None
        elif source.is_dir():
            shutil.copytree(source, destination, symlinks=True)
            digest = None
        else:
            shutil.copy2(source, destination)
            digest = _sha256(source)
        manifest.append(
            {
                "source": str(source),
                "backup": str(destination.relative_to(backup_root)),
                "sha256": digest,
            }
        )
    (backup_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _copy_source(
    source_root: Path, staging_data: Path
) -> tuple[list[Path], list[Path]]:
    copied: list[Path] = []
    skipped: list[Path] = []
    for source_file in sorted(
        path for path in source_root.rglob("*") if path.is_file()
    ):
        destination = _target_for_source(source_root, source_file, staging_data)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)
        copied.append(destination)
    return copied, skipped


def apply_project_migration(
    inspection: ArchledgerMigrationInspection,
    *,
    backup_dir: Path | None = None,
    retire_source: bool = False,
) -> ArchledgerMigrationResult:
    fresh = inspect_project_migration(
        inspection.project_root, source_config=inspection.source_config_path
    )
    if fresh.source_kind == "canonical" and not fresh.migration_required:
        return ArchledgerMigrationResult(
            fresh,
            fresh.backup_root,
            fresh.staging_root,
            fresh.target_migrations_dir / "canonical.json",
            (),
            (),
            (),
        )
    if not fresh.ready:
        blockers = "; ".join(
            issue.code for issue in fresh.issues if issue.severity == "blocker"
        )
        raise ConfigError(
            f"Project migration is blocked: {blockers}",
            details={"code": "ARCHLEDGER_MIGRATION_REQUIRED"},
        )
    if fresh.source_config_path is None or fresh.source_data_root is None:
        raise ConfigError(
            "Project migration has no source data.",
            details={"code": "ARCHLEDGER_MIGRATION_REQUIRED"},
        )
    backup_root = (backup_dir or fresh.backup_root).resolve()
    _backup(fresh, backup_root)
    staging_root = fresh.staging_root
    staging_root.mkdir(parents=True, exist_ok=False)
    staging_data = staging_root / "archledger"
    copied, skipped = _copy_source(fresh.source_data_root, staging_data)
    source_cfg = load_project_config(fresh.source_config_path)
    stable_cfg = _stable_config(source_cfg)
    staged_config = staging_root / "config.toml"
    write_text_atomic(staged_config, render_project_config(stable_cfg))

    target = fresh.target_data_root
    if target.exists():
        if any(target.iterdir()):
            raise ConfigError(
                f"Canonical target is not empty: {target}",
                details={"code": "ARCHLEDGER_DESTINATION_CONFLICT"},
            )
        target.rmdir()
    target.parent.mkdir(parents=True, exist_ok=True)
    staging_data.rename(target)

    if fresh.manifest_path.exists():
        manifest = load_manifest(fresh.manifest_path)
    else:
        manifest = new_manifest(
            project_uuid=fresh.canonical_project_uuid or source_cfg.project_uuid,
            project_name=source_cfg.project_name or fresh.project_root.name,
        )
    ensure_project_identity(
        manifest,
        project_uuid=fresh.canonical_project_uuid or source_cfg.project_uuid,
        project_name=source_cfg.project_name,
        default_name=fresh.project_root.name,
    )
    ensure_archledger_registration(manifest)
    write_text_atomic(
        fresh.stable_config_path, staged_config.read_text(encoding="utf-8")
    )
    write_manifest(fresh.manifest_path, manifest)
    # Initialize Ledgercore bindings.
    initialize_archledger_bindings(
        fresh.project_root,
        project_uuid=fresh.canonical_project_uuid or source_cfg.project_uuid,
        project_name=source_cfg.project_name or fresh.project_root.name,
        data_storage="project",
    )
    context = load_project_context(fresh.project_root)
    receipt = context.migrations_dir / (
        f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        "-ledgercore-0.4-repository-storage.json"
    )
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(
        json.dumps(
            {
                "kind": "archledger_project_migration",
                "version": 1,
                "source": str(fresh.source_data_root),
                "target": str(target),
                "backup": str(backup_root),
                "copied": [str(path) for path in copied],
                "uuid_evidence": list(fresh.uuid_evidence),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    retired: list[Path] = []
    if retire_source:
        suffix = f".migrated-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        for source in (*fresh.legacy_config_candidates, fresh.source_data_root):
            if source is None or not source.exists():
                continue
            destination = source.with_name(source.name + suffix)
            source.rename(destination)
            retired.append(destination)
    return ArchledgerMigrationResult(
        fresh,
        backup_root,
        staging_root,
        receipt,
        tuple(copied),
        tuple(skipped),
        tuple(retired),
    )


def inspection_payload(inspection: ArchledgerMigrationInspection) -> dict[str, object]:
    return {
        "kind": "archledger_project_migration_inspection",
        "schema_version": 1,
        "status": "ready" if inspection.ready else "blocked",
        "project": {
            "root": str(inspection.project_root),
            "uuid": inspection.canonical_project_uuid,
        },
        "source": {
            "kind": inspection.source_kind,
            "config": str(inspection.source_config_path)
            if inspection.source_config_path
            else None,
            "data_root": str(inspection.source_data_root)
            if inspection.source_data_root
            else None,
            "config_version": inspection.source_config_version,
        },
        "target": {
            "manifest": str(inspection.manifest_path),
            "config": str(inspection.stable_config_path),
            "mount_name": "data",
            "mount_storage": "repository",
            "data_root": str(inspection.target_data_root),
        },
        "counts": {
            "records": inspection.record_count,
            "sections": inspection.section_count,
            "archived_records": inspection.archived_record_count,
            "tombstones": inspection.tombstone_count,
        },
        "sequence": {
            "highest_number": inspection.highest_number,
            "stored_next_number": inspection.stored_next_number,
        },
        "changes": [
            {
                "source": str(item.source) if item.source else None,
                "destination": str(item.destination),
                "action": item.action,
            }
            for item in inspection.copy_items
        ],
        "issues": [
            {"severity": issue.severity, "code": issue.code, "message": issue.message}
            for issue in inspection.issues
        ],
        "commands": {"apply": "archledger migrate project --apply"},
    }


def migration_result_payload(result: ArchledgerMigrationResult) -> dict[str, object]:
    return {
        "inspection": inspection_payload(result.inspection),
        "backup_root": str(result.backup_root),
        "staging_root": str(result.staging_root),
        "receipt_path": str(result.receipt_path),
        "copied": [str(path) for path in result.copied],
        "skipped": [str(path) for path in result.skipped],
        "retired": [str(path) for path in result.retired],
    }
