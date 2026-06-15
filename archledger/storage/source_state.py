from __future__ import annotations

from pathlib import Path

from ledgercore.errors import JsonStoreError
from ledgercore.jsonio import load_json_object, write_json

from archledger.errors import StorageError
from archledger.metadata_version import require_version
from archledger.source_refs import RelativePosixPathError, validate_relative_posix_path
from archledger.source_tracking import (
    SOURCE_STATE_SCHEMA,
    DirectoryState,
    SourceState,
    TrackedFile,
)


def read_source_state(path: Path) -> SourceState | None:
    if not path.is_file():
        return None
    try:
        data = load_json_object(path, label="source-state JSON")
    except JsonStoreError as exc:
        raise StorageError(f"Invalid source-state JSON in {path}.") from exc
    return source_state_from_json(data)


def write_source_state(path: Path, state: SourceState) -> None:
    write_json(path, source_state_to_json(state))


def source_state_to_json(state: SourceState) -> dict[str, object]:
    return {
        "schema": state.schema,
        "project_uuid": state.project_uuid,
        "project_name": state.project_name,
        "version": state.version,
        "reason": state.reason,
        "scanner": dict(state.scanner),
        "files": {
            path: {
                "sha256": tracked.sha256,
            }
            for path, tracked in sorted(state.files.items())
        },
        "directories": {
            path: {
                "sha256": directory.sha256,
                "file_count": directory.file_count,
            }
            for path, directory in sorted(state.directories.items())
        },
    }


def source_state_from_json(data: object) -> SourceState:
    if not isinstance(data, dict):
        raise StorageError("source-state JSON must be an object.")
    schema = _require_string(data.get("schema"), "schema")
    if schema not in {SOURCE_STATE_SCHEMA, "archledger.source-state.v2"}:
        raise StorageError(f"Unsupported source-state schema: {schema}")
    project_uuid = _require_string(data.get("project_uuid"), "project_uuid")
    project_name = _require_string(data.get("project_name"), "project_name")
    version_value = data.get("version")
    if schema == "archledger.source-state.v2" and version_value is None:
        version_value = 1
    try:
        version = require_version(version_value)
    except ValueError as exc:
        raise StorageError(
            "source-state field version must be a positive integer."
        ) from exc
    reason = _require_string(data.get("reason"), "reason")
    scanner = _require_mapping(data.get("scanner"), "scanner")
    files_data = _require_mapping(data.get("files"), "files")
    directories = _directories_from_json(
        _require_mapping(data.get("directories"), "directories")
    )
    files: dict[str, TrackedFile] = {}
    for path, raw_entry in sorted(files_data.items()):
        candidate_path = path.replace("\\", "/")
        try:
            normalized_path = validate_relative_posix_path(
                candidate_path,
                field_name="source-state file paths",
            )
        except RelativePosixPathError as exc:
            raise StorageError(str(exc)) from exc
        entry = _require_mapping(raw_entry, f"files.{path}")
        files[normalized_path] = TrackedFile(
            path=normalized_path,
            sha256=_require_string(entry.get("sha256"), f"files.{path}.sha256"),
        )
    return SourceState(
        schema=SOURCE_STATE_SCHEMA,
        project_uuid=project_uuid,
        project_name=project_name,
        version=version,
        reason=reason,
        scanner=dict(scanner),
        files=files,
        directories=directories,
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


def _directories_from_json(data: dict[str, object]) -> dict[str, DirectoryState]:
    directories: dict[str, DirectoryState] = {}
    for path, raw_entry in sorted(data.items()):
        if path == ".":
            normalized_path = "."
        else:
            try:
                normalized_path = validate_relative_posix_path(
                    str(path),
                    field_name="source-state directory paths",
                )
            except RelativePosixPathError as exc:
                raise StorageError(str(exc)) from exc
        entry = _require_mapping(raw_entry, f"directories.{path}")
        directories[normalized_path] = DirectoryState(
            path=normalized_path,
            sha256=_require_string(entry.get("sha256"), f"directories.{path}.sha256"),
            file_count=_require_int(
                entry.get("file_count"),
                f"directories.{path}.file_count",
            ),
        )
    return directories
