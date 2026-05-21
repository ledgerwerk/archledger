from __future__ import annotations

import json
from pathlib import Path

from archledger.errors import StorageError
from archledger.source_refs import RelativePosixPathError, validate_relative_posix_path
from archledger.source_tracking import SOURCE_STATE_SCHEMA, SourceState, TrackedFile
from archledger.storage.common import read_text, write_text_atomic


def read_source_state(path: Path) -> SourceState | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise StorageError(f"Invalid source-state JSON in {path}.") from exc
    return source_state_from_json(data)


def write_source_state(path: Path, state: SourceState) -> None:
    write_text_atomic(
        path,
        json.dumps(source_state_to_json(state), indent=2, sort_keys=True) + "\n",
    )


def source_state_to_json(state: SourceState) -> dict[str, object]:
    return {
        "schema": state.schema,
        "project_uuid": state.project_uuid,
        "project_name": state.project_name,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "reason": state.reason,
        "scanner": dict(state.scanner),
        "files": {
            path: {
                "sha256": tracked.sha256,
                "size": tracked.size,
                "mtime_ns": tracked.mtime_ns,
            }
            for path, tracked in sorted(state.files.items())
        },
    }


def source_state_from_json(data: object) -> SourceState:
    if not isinstance(data, dict):
        raise StorageError("source-state JSON must be an object.")
    schema = _require_string(data.get("schema"), "schema")
    if schema != SOURCE_STATE_SCHEMA:
        raise StorageError(f"Unsupported source-state schema: {schema}")
    project_uuid = _require_string(data.get("project_uuid"), "project_uuid")
    project_name = _require_string(data.get("project_name"), "project_name")
    created_at = _require_string(data.get("created_at"), "created_at")
    updated_at = _require_string(data.get("updated_at"), "updated_at")
    reason = _require_string(data.get("reason"), "reason")
    scanner = _require_mapping(data.get("scanner"), "scanner")
    files_data = _require_mapping(data.get("files"), "files")
    files: dict[str, TrackedFile] = {}
    for path, raw_entry in sorted(files_data.items()):
        try:
            normalized_path = validate_relative_posix_path(
                path,
                field_name="source-state file paths",
            )
        except RelativePosixPathError as exc:
            raise StorageError(str(exc)) from exc
        entry = _require_mapping(raw_entry, f"files.{path}")
        files[normalized_path] = TrackedFile(
            path=normalized_path,
            sha256=_require_string(entry.get("sha256"), f"files.{path}.sha256"),
            size=_require_int(entry.get("size"), f"files.{path}.size"),
            mtime_ns=_require_int(entry.get("mtime_ns"), f"files.{path}.mtime_ns"),
        )
    return SourceState(
        schema=schema,
        project_uuid=project_uuid,
        project_name=project_name,
        created_at=created_at,
        updated_at=updated_at,
        reason=reason,
        scanner=dict(scanner),
        files=files,
    )


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StorageError(
            f"source-state field {field_name} must be a non-empty string."
        )
    return value.strip()


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StorageError(f"source-state field {field_name} must be an integer.")
    return value


def _require_mapping(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise StorageError(f"source-state field {field_name} must be an object.")
    normalized: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise StorageError(f"source-state field {field_name} must use string keys.")
        normalized[key] = item
    return normalized
