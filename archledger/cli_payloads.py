from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeVar

from archledger.converters import BuildResult
from archledger.ids import (
    DEFAULT_ID_PREFIX,
    DEFAULT_ID_SEGMENT_MODE,
    DEFAULT_ID_WIDTH,
    LedgerIdFormat,
    format_ledger_id,
    format_local_id,
    global_ref_for,
    ref_for,
)
from archledger.migration import MigrationResult
from archledger.model import (
    MAJOR_SECTION_SPECS,
    VALID_OUTPUT_FORMATS,
    VALID_SOURCE_FORMATS,
    VALID_STATUSES,
    ArchitectureRecord,
    is_visible_status,
    normalize_kind,
)
from archledger.record_types import RECORD_TYPE_SPECS
from archledger.renumber import RenumberResult
from archledger.repository import (
    ArchitectureRepository,
    ArchiveResult,
    CheckFinding,
    CheckResult,
    DoctorResult,
    InitResult,
    StatusResult,
)
from archledger.source_tracking import (
    ChangedFile,
    ChangeSet,
    ImpactedRecord,
    SourceState,
)
from archledger.storage.paths import ProjectPaths
from archledger.storage.project_config import ProjectConfig

T = TypeVar("T")
# --- Shared payload helpers ---


def _record_identity(
    record: ArchitectureRecord,
    config: ProjectConfig,
) -> dict[str, object]:
    """Core identity fields shared by most record payloads."""
    return {
        "id": record.id,
        "kind": record.kind,
        "type": record.type,
        "ref": ref_for(record, config),
        "title": record.title,
        "status": record.status,
        "section": record.section,
        "path": str(record.path),
    }


def _record_detail(
    record: ArchitectureRecord,
    config: ProjectConfig,
    *,
    include_body: bool = False,
    workspace_root: Path | None = None,
) -> dict[str, object]:
    """Extended record payload with metadata and optional body."""
    payload = _record_identity(record, config)
    if workspace_root is not None:
        payload["path"] = display_path(workspace_root, record.path)
    payload["metadata"] = record.metadata
    if include_body:
        payload["body"] = record.body
    return payload


def _findings_payload(
    errors: Sequence[T],
    warnings: Sequence[T],
    *,
    serializer: Callable[[T], dict[str, object]] | None = None,
) -> dict[str, object]:
    """Standard errors/warnings findings payload."""
    if serializer is not None:
        return {
            "errors": [serializer(f) for f in errors],
            "warnings": [serializer(f) for f in warnings],
        }
    return {"errors": list(errors), "warnings": list(warnings)}


def init_result_payload(result: InitResult) -> dict[str, object]:
    return {
        "workspace_root": str(result.workspace_root),
        "config_path": str(result.config_path),
        "archledger_dir": str(result.archledger_dir),
        "created_paths": [str(path) for path in result.created_paths],
    }


def status_payload(
    repo: ArchitectureRepository,
    paths: ProjectPaths,
    config: ProjectConfig,
) -> dict[str, object]:
    status_result: StatusResult = repo.status()
    return {
        "workspace_root": str(status_result.workspace_root),
        "config_path": str(status_result.config_path),
        "archledger_dir": str(status_result.archledger_dir),
        "archive_dir": str(status_result.archive_dir),
        "storage_meta_path": str(status_result.storage_meta_path),
        "build_dir": str(status_result.build_dir),
        "sections_count": status_result.sections_count,
        "record_directories_count": status_result.record_directories_count,
        "project_name": config.project_name,
        "project_uuid": config.project_uuid,
    }


def where_payload(
    repo: ArchitectureRepository,
    paths: ProjectPaths,
    config: ProjectConfig,
) -> dict[str, object]:
    del repo, config
    return {
        "workspace_root": str(paths.workspace_root),
        "config_path": str(paths.config_path),
        "archledger_dir": str(paths.archledger_dir),
        "sections_dir": str(paths.sections_dir),
        "records_dir": str(paths.records_dir),
        "archive_dir": str(paths.archive_dir),
        "build_dir": str(paths.build_dir),
        "storage_meta_path": str(paths.storage_meta_path),
        "source_state_path": str(paths.source_state_path),
    }


def schema_payload(
    repo: ArchitectureRepository,
    paths: ProjectPaths,
    config: ProjectConfig,
) -> dict[str, object]:
    del repo, paths
    return {
        "schema": "archledger.schema.v1",
        "record_types": [
            {
                "kind": spec.kind,
                "aliases": list(spec.aliases),
                "default_section": spec.default_section,
                "directory": spec.directory,
            }
            for spec in RECORD_TYPE_SPECS
        ],
        "id_strategy": "ledger-wide-local-resource-id",
        "id_format": {
            "ledger_code": config.ledger_code,
            "width": config.id_width,
        },
        "id_pattern": "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*-\\d{4,}$",
        "reserved_section_ids": {
            section.key: format_local_id(
                config.id_kind_map.get("section", config.id_default_kind),
                section.number,
                width=config.id_width,
            )
            for section in MAJOR_SECTION_SPECS
        },
        "statuses": sorted(VALID_STATUSES),
        "sections": [
            {
                "key": section.key,
                "title": section.title,
                "order": section.order,
            }
            for section in MAJOR_SECTION_SPECS
        ],
        "source_formats": sorted(VALID_SOURCE_FORMATS),
        "output_formats": sorted(VALID_OUTPUT_FORMATS),
    }


def new_record_payload(
    record: ArchitectureRecord,
    config: ProjectConfig,
) -> dict[str, object]:
    return {
        "id": record.id,
        "kind": record.kind,
        "type": record.type,
        "ref": global_ref_for(record.id, config.ledger_code, width=config.id_width),
        "path": str(record.path),
    }


def seed_payload(
    preset: str,
    records: list[ArchitectureRecord],
    config: ProjectConfig,
) -> dict[str, object]:
    return {
        "preset": preset,
        "records": [
            {
                "id": record.id,
                "kind": record.kind,
                "type": record.type,
                "ref": global_ref_for(
                    record.id, config.ledger_code, width=config.id_width
                ),
                "path": str(record.path),
            }
            for record in records
        ],
    }


def list_records_payload(
    records: list[ArchitectureRecord],
    config: ProjectConfig,
) -> dict[str, object]:
    return {"records": [_record_identity(record, config) for record in records]}


def show_record_payload(
    record: ArchitectureRecord,
    config: ProjectConfig,
) -> dict[str, object]:
    return _record_detail(
        record,
        config,
        include_body=True,
    )


def read_payload(
    repo: ArchitectureRepository,
    paths: ProjectPaths,
    config: ProjectConfig,
    *,
    include_body: bool,
    include_draft: bool,
    include_superseded: bool,
    section: str | None,
    kind: str | None,
    scope: str | None = None,
    scope_kind: str | None = None,
    addon: str | None = None,
) -> dict[str, object]:
    from archledger.scopes import VALID_SCOPE_KINDS

    normalized_kind = None
    if kind is not None:
        normalized_kind = (
            "section" if kind.strip().lower() == "section" else normalize_kind(kind)
        )
    records = []
    for record in repo.load_all_records(include_sections=True):
        if record.type != "section" and not is_visible_status(
            record.status,
            include_draft=include_draft,
            include_superseded=include_superseded,
        ):
            continue
        if section is not None and record.section != section:
            continue
        if normalized_kind is not None and record.type != normalized_kind:
            continue
        if scope is not None or scope_kind is not None or addon is not None:
            if record.scope is None:
                continue
            if scope is not None and record.scope.name != scope:
                continue
            if scope_kind is not None:
                if scope_kind not in VALID_SCOPE_KINDS:
                    continue
                if record.scope.kind != scope_kind:
                    continue
            if addon is not None:
                addon_dir = addon if addon.endswith("/") else addon + "/"
                if not any(
                    addon_dir == apply_to
                    or addon_dir.startswith(apply_to.rstrip("/") + "/")
                    or apply_to.rstrip("/") == addon
                    for apply_to in record.scope.applies_to
                ):
                    continue
        item: dict[str, object] = {
            "id": record.id,
            "kind": record.kind,
            "type": record.type,
            "ref": global_ref_for(record.id, config.ledger_code, width=config.id_width),
            "title": record.title,
            "status": record.status,
            "section": record.section,
            "order": record.order,
            "path": display_path(paths.workspace_root, record.path),
            "body_format": record.metadata.get("body_format", config.source_format),
            "metadata": record.metadata,
        }
        if include_body:
            item["body"] = record.body
        records.append(item)
    return {
        "schema": "archledger.read.v1",
        "project": {
            "name": config.project_name,
            "uuid": config.project_uuid,
            "source_format": config.source_format,
            "source_schema_version": config.source_schema_version,
            "arc42_template_version": config.arc42_template_version,
        },
        "paths": {
            "workspace_root": str(paths.workspace_root),
            "config_path": str(paths.config_path),
            "archledger_dir": str(paths.archledger_dir),
            "sections_dir": str(paths.sections_dir),
            "records_dir": str(paths.records_dir),
            "archive_dir": str(paths.archive_dir),
        },
        "records": records,
    }


def snapshot_payload(paths: ProjectPaths, state: SourceState) -> dict[str, object]:
    return {
        "schema": "archledger.snapshot.v2",
        "source_state_path": str(paths.source_state_path),
        "reason": state.reason,
        "scanner_used": state.scanner.get("used", "filesystem"),
        "file_count": len(state.files),
        "version": state.version,
    }


def changed_payload(
    paths: ProjectPaths,
    changes: ChangeSet,
    config: ProjectConfig,
) -> dict[str, object]:
    baseline: dict[str, object] = {"exists": changes.baseline_exists}
    if changes.baseline_exists:
        baseline["version"] = changes.baseline_version
        baseline["reason"] = changes.baseline_reason
    return {
        "schema": "archledger.changed.v2",
        "baseline": baseline,
        "scan": {
            "version": changes.current_version,
            "scanner_used": changes.scanner_used,
            "file_count": changes.file_count,
        },
        "changes": {
            "added": [
                changed_file_payload(item)
                for item in changes.changed_files
                if item.change == "added"
            ],
            "modified": [
                changed_file_payload(item)
                for item in changes.changed_files
                if item.change == "modified"
            ],
            "deleted": [
                changed_file_payload(item)
                for item in changes.changed_files
                if item.change == "deleted"
            ],
            "possible_renames": [
                {
                    "old_path": item.old_path,
                    "new_path": item.new_path,
                    "sha256": item.sha256,
                }
                for item in changes.possible_renames
            ],
            "unbaselined_files": list(changes.unbaselined_files),
        },
        "impact": {
            "records": [
                impacted_record_payload(paths, item, config)
                for item in changes.impacted_records
            ],
            "sections": list(changes.impacted_sections),
            "unlinked_changed_files": list(changes.unlinked_changed_files),
        },
    }


def changed_file_payload(item: ChangedFile) -> dict[str, object]:
    payload: dict[str, object] = {
        "path": item.path,
        "change": item.change,
    }
    if item.old_sha256 is not None:
        payload["old_sha256"] = item.old_sha256
    if item.new_sha256 is not None:
        payload["new_sha256"] = item.new_sha256
    return payload


def impacted_record_payload(
    paths: ProjectPaths,
    item: ImpactedRecord,
    config: ProjectConfig,
) -> dict[str, object]:
    return {
        "id": item.id,
        "kind": getattr(item, "kind", item.type),
        "type": item.type,
        "ref": ref_for(item.id, config),
        "title": item.title,
        "status": item.status,
        "section": item.section,
        "path": display_path(paths.workspace_root, Path(item.path)),
        "matched_refs": list(item.matched_refs),
    }


def check_payload(result: CheckResult) -> dict[str, object]:
    return _findings_payload(result.errors, result.warnings, serializer=finding_payload)


def archive_payload(result: ArchiveResult) -> dict[str, object]:
    return {
        "id": result.record_id,
        "from": str(result.source_path),
        "to": str(result.archive_path),
        "reason": result.reason,
        "already_archived": result.already_archived,
    }


def doctor_payload(
    result: DoctorResult,
    *,
    id_format: LedgerIdFormat | None = None,
    id_prefix: str = DEFAULT_ID_PREFIX,
    id_width: int = DEFAULT_ID_WIDTH,
    id_segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
) -> dict[str, object]:
    resolved_format = (
        LedgerIdFormat(
            prefix=id_prefix,
            width=id_width,
            segment_mode=id_segment_mode,
        )
        if id_format is None
        else id_format
    )
    return {
        "schema": "archledger.doctor.v1",
        **_findings_payload(result.errors, result.warnings, serializer=finding_payload),
        "repairs": [
            {
                "kind": repair.kind,
                "message": repair.message,
                **({"path": str(repair.path)} if repair.path else {}),
                **({"before": repair.before} if repair.before is not None else {}),
                **({"after": repair.after} if repair.after is not None else {}),
            }
            for repair in result.repairs
        ],
        "ledger": {
            "highest_seen": result.highest_seen,
            "storage_next_number_before": result.storage_next_number_before,
            "storage_next_number_after": result.storage_next_number_after,
            "missing_ids": [
                _display_ledger_number(n, resolved_format)
                for n in result.missing_numbers
            ],
            "duplicate_ids": [
                _display_ledger_number(n, resolved_format)
                for n in result.duplicate_numbers
            ],
        },
    }


def renumber_payload(result: RenumberResult) -> dict[str, object]:
    return {
        "schema": "archledger.renumber.v1",
        "apply": result.apply,
        "old_format": {
            "prefix": result.old_prefix,
            "width": result.old_width,
            "segment_mode": result.old_segment_mode,
        },
        "new_format": {
            "prefix": result.new_prefix,
            "width": result.new_width,
            "segment_mode": result.new_segment_mode,
        },
        "renamed_count": len(result.renamed),
        "rewritten_count": len(result.rewritten),
        "renamed": [
            {
                "old_id": item.old_id,
                "new_id": item.new_id,
                "from": str(item.old_path),
                "to": str(item.new_path),
            }
            for item in result.renamed
        ],
        "rewritten": [
            {
                "path": str(item.path),
                "replacement_count": item.replacement_count,
            }
            for item in result.rewritten
        ],
        "quarantined_generated_tombstones_count": len(
            result.quarantined_generated_tombstones
        ),
        "quarantined_generated_tombstones": [
            {
                "path": str(item.path),
                "quarantine_path": str(item.quarantine_path),
                "reason": item.reason,
            }
            for item in result.quarantined_generated_tombstones
        ],
        "config_path": str(result.config_path),
        "storage_next_number_before": result.storage_next_number_before,
        "storage_next_number_after": result.storage_next_number_after,
    }


def finding_payload(finding: CheckFinding) -> dict[str, object]:
    payload: dict[str, object] = {"level": finding.level, "message": finding.message}
    if finding.path is not None:
        payload["path"] = str(finding.path)
    return payload


def _display_ledger_number(number: int, id_format: LedgerIdFormat) -> str:
    if id_format.segment_mode == "none":
        return format_ledger_id(
            number,
            prefix=id_format.prefix,
            width=id_format.width,
        )
    return f"{id_format.prefix}_<segment>_{number:0{id_format.width}d}"


def build_result_payload(result: BuildResult) -> dict[str, object]:
    return {
        "assembled_path": str(result.assembled_path),
        "outputs": [
            {
                "format": output_result.format,
                "output_path": str(output_result.output_path),
            }
            for output_result in result.outputs
        ],
    }


def convert_sources_payload(result: MigrationResult) -> dict[str, object]:
    return {
        "target_format": result.target_format,
        "write": result.write,
        "replace": result.replace,
        "config_path": str(result.config_path),
        "converted": [
            {
                "source_path": str(item.source_path),
                "output_path": str(item.output_path),
                "body_format": item.body_format,
            }
            for item in result.converted
        ],
        "warnings": list(result.warnings),
    }


def display_path(workspace_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def profile_migration_payload(result: object) -> dict[str, object]:
    """Payload for profile migrate/enable/disable commands."""
    return {
        "schema": "archledger.profile-migration.v1",
        "profile": result.profile,
        "write": result.write,
        "changed": result.changed,
        "steps": [
            {
                "action": step.action,
                **({"source": step.source} if step.source else {}),
                **({"target": step.target} if step.target else {}),
                "message": step.message,
            }
            for step in result.steps
        ],
        "warnings": list(getattr(result, "warnings", ()) or ()),
    }


def profile_list_payload(summary: dict[str, object]) -> dict[str, object]:
    """Payload for profile list command."""
    return {
        "schema": "archledger.profile-list.v1",
        **summary,
    }
