from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from ledgercore.config import LedgerProjectLocator, locate_ledger_project
from ledgercore.errors import LedgerCoreError
from ledgercore.layout import (
    LedgerLocalConfig,
    LedgerProjectManifest,
    ResolvedLedgerLayout,
    ResolvedMount,
    parse_ledger_local_config,
    parse_ledger_project_manifest,
    resolve_ledger_layout,
)

from archledger.config.model import ProjectConfig
from archledger.config.parse import load_project_config
from archledger.errors import ConfigError, StorageError
from archledger.storage.common import read_text
from archledger.storage.meta import read_storage_meta
from archledger.storage.paths import ProjectPaths

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found, unused-ignore]

ProjectStateKind = Literal["uninitialized", "legacy", "canonical", "partial", "invalid"]
MANIFEST_PATH = Path(".ledger/ledger.toml")
LOCAL_CONFIG_PATH = Path(".ledger/ledger.local.toml")
ARCHLEDGER_CONFIG_PATH = Path(".ledger/arch/config.toml")
ARCHLEDGER_DATA_PATH = Path(".ledger/arch/archledger")


@dataclass(frozen=True, slots=True)
class ArchledgerProjectContext:
    project_root: Path
    config_root: Path
    manifest_path: Path
    local_config_path: Path
    config_path: Path
    data_root: Path
    sections_dir: Path
    records_dir: Path
    archive_dir: Path
    migrations_dir: Path
    build_dir: Path
    storage_meta_path: Path
    source_state_path: Path
    document_state_path: Path
    project_uuid: str
    project_name: str | None
    active_mount_name: Literal["data"] = "data"
    mount_storage: Literal["repository"] = "repository"
    mount_scope: None = None
    mount_source: Literal["repository"] = "repository"
    config: ProjectConfig | None = None
    layout: ResolvedLedgerLayout | None = None

    @property
    def workspace_root(self) -> Path:
        return self.project_root

    @property
    def archledger_dir(self) -> Path:
        return self.data_root

    def project_paths(self) -> ProjectPaths:
        if self.config is None:
            raise ConfigError("Canonical Archledger configuration is not loaded.")
        return ProjectPaths(
            workspace_root=self.project_root,
            config_root=self.config_root,
            manifest_path=self.manifest_path,
            local_config_path=self.local_config_path,
            config_path=self.config_path,
            archledger_dir=self.data_root,
            sections_dir=self.sections_dir,
            records_dir=self.records_dir,
            archive_dir=self.archive_dir,
            build_dir=self.build_dir,
            storage_meta_path=self.storage_meta_path,
            source_state_path=self.source_state_path,
            document_state_path=self.document_state_path,
            mount_name=self.active_mount_name,
            mount_storage=self.mount_storage,
            mount_scope=self.mount_scope,
            mount_source=self.mount_source,
        )


def _error(message: str, code: str) -> ConfigError:
    return ConfigError(message, details={"code": code})


def _load_toml(path: Path) -> dict[str, object]:
    try:
        value = tomllib.loads(read_text(path))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise _error(
            f"Failed to parse {path}: {exc}", "ARCHLEDGER_MANIFEST_INVALID"
        ) from exc
    if not isinstance(value, dict):
        raise _error(
            f"{path} did not parse to a TOML table.", "ARCHLEDGER_MANIFEST_INVALID"
        )
    return value


def _manifest_registration(
    manifest: LedgerProjectManifest,
) -> tuple[object, ResolvedMount | object]:
    registration = manifest.ledgers.get("archledger")
    if registration is None:
        raise _error(
            "The shared manifest has no Archledger registration. Run: archledger init",
            "ARCHLEDGER_REGISTRATION_MISSING",
        )
    if registration.config is None or registration.config.path != "arch/config.toml":
        raise _error(
            "Archledger must use project config path arch/config.toml.",
            "ARCHLEDGER_REGISTRATION_CONFLICT",
        )
    if set(registration.mounts) != {"data"}:
        raise _error(
            "Archledger must define exactly one mount named data.",
            "ARCHLEDGER_REGISTRATION_CONFLICT",
        )
    mount = registration.mounts["data"]
    if (
        mount.storage != "repository"
        or mount.scope is not None
        or mount.path != "arch/archledger"
    ):
        raise _error(
            "Archledger data must use an unscoped repository mount at arch/archledger.",
            "ARCHLEDGER_REGISTRATION_CONFLICT",
        )
    return registration, mount


def _load_local_config(locator: LedgerProjectLocator) -> LedgerLocalConfig | None:
    path = locator.local_config_path
    if not path.is_file():
        return None
    try:
        return parse_ledger_local_config(
            _load_toml(path), project_root=locator.project_root
        )
    except LedgerCoreError as exc:
        raise _error(
            f"Invalid shared local Ledger configuration: {exc}",
            "ARCHLEDGER_MANIFEST_INVALID",
        ) from exc


def load_project_context(
    start: Path,
    *,
    require_initialized: bool = True,
    environ: Mapping[str, str] | None = None,
) -> ArchledgerProjectContext:
    locator = locate_ledger_project(
        start, legacy_tool_filenames=("archledger.toml", ".archledger.toml")
    )
    if locator is None:
        raise _error(
            "No .ledger/ledger.toml found. Run: archledger init",
            "ARCHLEDGER_PROJECT_NOT_FOUND",
        )
    if locator.is_legacy:
        raise _error(
            "Legacy Archledger layout found. Run: archledger migrate project",
            "ARCHLEDGER_MIGRATION_REQUIRED",
        )
    try:
        manifest = parse_ledger_project_manifest(_load_toml(locator.manifest_path))
        _manifest_registration(manifest)
        local_config = _load_local_config(locator)
        layout = resolve_ledger_layout(
            locator,
            manifest,
            "archledger",
            local_config=local_config,
            environ=os.environ if environ is None else environ,
        )
    except LedgerCoreError as exc:
        code = (
            "ARCHLEDGER_REGISTRATION_CONFLICT"
            if "registration" in str(exc).lower()
            else "ARCHLEDGER_MANIFEST_INVALID"
        )
        raise _error(f"Invalid Archledger project layout: {exc}", code) from exc

    mount = layout.mounts.get("data")
    expected_data = (locator.project_root / ARCHLEDGER_DATA_PATH).resolve(strict=False)
    if (
        mount is None
        or mount.storage != "repository"
        or mount.source != "repository"
        or mount.path != expected_data
    ):
        raise _error(
            "Ledgercore resolved Archledger data outside .ledger/arch/archledger.",
            "ARCHLEDGER_DATA_ROOT_CONFLICT",
        )
    config_path = layout.tool_config_path
    expected_config = (locator.project_root / ARCHLEDGER_CONFIG_PATH).resolve(
        strict=False
    )
    if config_path is None or config_path.resolve(strict=False) != expected_config:
        raise _error(
            "Ledgercore resolved an unexpected Archledger config path.",
            "ARCHLEDGER_REGISTRATION_CONFLICT",
        )
    try:
        config = load_project_config(config_path)
    except ConfigError as exc:
        raise _error(str(exc), "ARCHLEDGER_CONFIG_INVALID") from exc
    if config.config_version != 11:
        raise _error(
            "Archledger stable configuration must use config_version 11.",
            "ARCHLEDGER_CONFIG_INVALID",
        )
    config = replace(
        config,
        archledger_dir=str(mount.path),
        project_uuid=manifest.project_uuid,
        project_name=manifest.project_name or locator.project_root.name,
    )
    paths = _resolve_paths(locator.project_root, config_path, mount, config)
    if require_initialized:
        if not paths.archledger_dir.is_dir():
            raise _error(
                "Canonical Archledger data root is missing.",
                "ARCHLEDGER_DATA_ROOT_MISSING",
            )
        try:
            meta = read_storage_meta(paths.storage_meta_path)
        except (OSError, StorageError) as exc:
            raise _error(
                f"Canonical Archledger storage is invalid: {exc}",
                "ARCHLEDGER_STORAGE_INVALID",
            ) from exc
        if meta.project_uuid != manifest.project_uuid:
            raise _error(
                "storage.yaml project_uuid does not match the shared manifest.",
                "ARCHLEDGER_STORAGE_UUID_MISMATCH",
            )
    return ArchledgerProjectContext(
        project_root=locator.project_root.resolve(),
        config_root=locator.config_root.resolve(),
        manifest_path=locator.manifest_path.resolve(),
        local_config_path=locator.local_config_path.resolve(),
        config_path=config_path.resolve(),
        data_root=mount.path,
        sections_dir=paths.sections_dir,
        records_dir=paths.records_dir,
        archive_dir=paths.archive_dir,
        migrations_dir=mount.path / "migrations",
        build_dir=paths.build_dir,
        storage_meta_path=paths.storage_meta_path,
        source_state_path=paths.source_state_path,
        document_state_path=mount.path / "document-state.json",
        project_uuid=manifest.project_uuid,
        project_name=manifest.project_name,
        config=config,
        layout=layout,
    )


def _resolve_paths(
    project_root: Path, config_path: Path, mount: ResolvedMount, config: ProjectConfig
) -> ProjectPaths:
    data_root = mount.path
    build_raw = config.build_output_dir
    build_dir = (
        project_root
        if build_raw == "."
        else _inside(project_root, build_raw, "build.default_output_dir")
    )
    _inside(build_dir, config.build_default_output, "build.default_output")
    _inside(build_dir, config.diagram_output_dir, "diagrams.output_dir")
    sections_dir = _inside(
        data_root, config.profiles.arc42.sections_dir, "profiles.arc42.sections_dir"
    )
    state_path = _inside(data_root, config.tracking_state_file, "tracking.state_file")
    return ProjectPaths(
        workspace_root=project_root,
        config_root=project_root / ".ledger",
        manifest_path=project_root / MANIFEST_PATH,
        local_config_path=project_root / LOCAL_CONFIG_PATH,
        config_path=config_path,
        archledger_dir=data_root,
        sections_dir=sections_dir,
        records_dir=data_root / "records",
        archive_dir=data_root / "archive",
        build_dir=build_dir,
        storage_meta_path=data_root / "storage.yaml",
        source_state_path=state_path,
        document_state_path=data_root / "document-state.json",
    )


def _inside(base: Path, value: str, field_name: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else base / candidate).resolve(
        strict=False
    )
    try:
        resolved.relative_to(base.resolve(strict=False))
    except ValueError as exc:
        raise _error(
            f"{field_name} must stay inside {base}.", "ARCHLEDGER_CONFIG_INVALID"
        ) from exc
    return resolved


def classify_project_state(start: Path) -> ProjectStateKind:
    locator = locate_ledger_project(
        start, legacy_tool_filenames=("archledger.toml", ".archledger.toml")
    )
    if locator is None:
        return "uninitialized"
    if locator.is_legacy:
        return "legacy"
    try:
        load_project_context(start)
    except ConfigError as exc:
        return (
            "partial"
            if exc.details.get("code")
            in {
                "ARCHLEDGER_DATA_ROOT_MISSING",
                "ARCHLEDGER_CONFIG_MISSING",
                "ARCHLEDGER_STORAGE_INVALID",
            }
            else "invalid"
        )
    return "canonical"


__all__ = [
    "ARCHLEDGER_CONFIG_PATH",
    "ARCHLEDGER_DATA_PATH",
    "ArchledgerProjectContext",
    "ProjectStateKind",
    "classify_project_state",
    "load_project_context",
]
