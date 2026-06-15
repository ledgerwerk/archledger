from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from ledgercore.jsonio import load_json_object, write_json

from archledger.config import ProjectConfig, render_project_config
from archledger.metadata_version import metadata_version
from archledger.storage.common import write_text_atomic
from archledger.storage.frontmatter import (
    iter_source_files,
    read_front_matter_document,
    write_front_matter_document,
)
from archledger.storage.meta import read_storage_meta, write_storage_meta
from archledger.storage.paths import ProjectPaths

LEGACY_TIMESTAMP_FIELDS = ("date", "created_at", "updated_at", "archived_at")


@dataclass(frozen=True, slots=True)
class MetadataSourceChange:
    path: str
    removed_fields: tuple[str, ...]
    added_fields: dict[str, object]
    schema_version_before: object
    schema_version_after: int


@dataclass(frozen=True, slots=True)
class MetadataMigrationResult:
    apply: bool
    target: str
    records_seen: int
    changes: tuple[MetadataSourceChange, ...]
    storage_changed: bool
    source_state_changed: bool
    config_changed: bool


def migrate_metadata(
    paths: ProjectPaths,
    config: ProjectConfig,
    *,
    apply: bool,
) -> MetadataMigrationResult:
    source_paths = sorted(
        {
            *iter_source_files(
                paths.sections_dir,
                (config.section_extension, config.record_extension),
            ),
            *iter_source_files(
                paths.records_dir,
                (config.section_extension, config.record_extension),
            ),
            *iter_source_files(
                paths.archive_dir,
                (config.section_extension, config.record_extension),
            ),
        }
    )
    changes: list[MetadataSourceChange] = []
    for path in source_paths:
        metadata, body = read_front_matter_document(path)
        migrated = dict(metadata)
        removed = tuple(field for field in LEGACY_TIMESTAMP_FIELDS if field in migrated)
        for field in removed:
            migrated.pop(field, None)
        added: dict[str, object] = {}
        if "version" not in migrated:
            migrated["version"] = 1
            added["version"] = 1
        before_schema = migrated.get("schema_version")
        migrated["schema_version"] = 4
        if migrated == metadata:
            continue
        changes.append(
            MetadataSourceChange(
                path=path.relative_to(paths.workspace_root).as_posix(),
                removed_fields=removed,
                added_fields=added,
                schema_version_before=before_schema,
                schema_version_after=4,
            )
        )
        if apply:
            write_front_matter_document(path, migrated, body)

    meta = read_storage_meta(paths.storage_meta_path)
    storage_changed = meta.storage_version != 3 or not _storage_is_current(
        paths.storage_meta_path
    )
    if apply and storage_changed:
        write_storage_meta(
            paths.storage_meta_path,
            replace(
                meta,
                storage_version=3,
                version=metadata_version({"version": meta.version}),
            ),
        )

    source_state_changed = _migrate_source_state(paths.source_state_path, apply=apply)
    config_changed = config.config_version != 10 or config.source_schema_version != 4
    if apply and config_changed:
        write_text_atomic(
            paths.config_path,
            render_project_config(
                replace(config, config_version=10, source_schema_version=4)
            ),
        )
    return MetadataMigrationResult(
        apply=apply,
        target="versioned",
        records_seen=len(source_paths),
        changes=tuple(changes),
        storage_changed=storage_changed,
        source_state_changed=source_state_changed,
        config_changed=config_changed,
    )


def metadata_migration_payload(
    result: MetadataMigrationResult,
) -> dict[str, object]:
    return {
        "schema": "archledger.migrate-metadata.v1",
        "apply": result.apply,
        "target": result.target,
        "records_seen": result.records_seen,
        "records_changed": len(result.changes),
        "storage_changed": result.storage_changed,
        "source_state_changed": result.source_state_changed,
        "config_changed": result.config_changed,
        "changes": [
            {
                "path": change.path,
                "removed_fields": list(change.removed_fields),
                "added_fields": change.added_fields,
                "schema_version_before": change.schema_version_before,
                "schema_version_after": change.schema_version_after,
            }
            for change in result.changes
        ],
    }


def _storage_is_current(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return "storage_version: 3" in text and "created_at:" not in text


def _migrate_source_state(path: Path, *, apply: bool) -> bool:
    if not path.is_file():
        return False
    data = load_json_object(path, label="source-state JSON")
    migrated = dict(data)
    for field in ("created_at", "updated_at"):
        migrated.pop(field, None)
    migrated["schema"] = "archledger.source-state.v3"
    migrated.setdefault("version", 1)
    changed = migrated != data
    if apply and changed:
        write_json(path, migrated)
    return changed
