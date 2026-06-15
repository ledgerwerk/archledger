from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from ledgercore.errors import IdFormatError
from ledgercore.errors import StorageError as CoreStorageError
from ledgercore.refs import parse_local_ref
from ledgercore.yamlio import load_yaml_object, write_yaml

from archledger.errors import StorageError
from archledger.metadata_version import require_version
from archledger.model import SOURCE_FORMAT_EXTENSIONS


@dataclass(frozen=True, slots=True)
class StorageMeta:
    storage_version: int
    created_with_archledger: str
    project_uuid: str
    version: int
    next_number: int


def default_storage_meta(project_uuid: str, archledger_version: str) -> StorageMeta:
    return StorageMeta(
        storage_version=3,
        created_with_archledger=archledger_version,
        project_uuid=project_uuid,
        version=1,
        next_number=1,
    )


def read_storage_meta(path: Path) -> StorageMeta:
    if not path.is_file():
        raise StorageError(f"Missing storage metadata file: {path}")
    try:
        raw_data = load_yaml_object(path, label="storage.yaml")
    except CoreStorageError as exc:
        raise StorageError(f"Failed to parse storage metadata: {path}") from exc

    storage_version = raw_data.get("storage_version")
    created_with_archledger = raw_data.get("created_with_archledger")
    project_uuid = raw_data.get("project_uuid")
    version = raw_data.get("version")
    next_number = raw_data.get("next_number")

    if storage_version not in {2, 3}:
        raise StorageError("storage_version must be 2 or 3.")
    if not all(
        isinstance(value, str) and value
        for value in (created_with_archledger, project_uuid)
    ):
        raise StorageError(
            "storage.yaml created_with_archledger and project_uuid "
            "must be non-empty strings."
        )
    if storage_version == 2 and version is None:
        version = 1
    try:
        validated_version = require_version(version)
    except ValueError as exc:
        raise StorageError("storage.yaml version must be a positive integer.") from exc
    if (
        isinstance(next_number, bool)
        or not isinstance(next_number, int)
        or next_number < 1
    ):
        raise StorageError("storage.yaml next_number must be a positive integer.")

    return StorageMeta(
        storage_version=storage_version,
        created_with_archledger=cast(str, created_with_archledger),
        project_uuid=cast(str, project_uuid),
        version=validated_version,
        next_number=next_number,
    )


def write_storage_meta(path: Path, meta: StorageMeta) -> None:
    write_yaml(
        path,
        {
            "storage_version": 3,
            "created_with_archledger": meta.created_with_archledger,
            "project_uuid": meta.project_uuid,
            "version": meta.version,
            "next_number": meta.next_number,
        },
        sort_keys=False,
    )


def recompute_next_number(
    archledger_dir: Path,
    *,
    source_extensions: tuple[str, ...] = (),
) -> int:
    known_extensions = {
        *SOURCE_FORMAT_EXTENSIONS.values(),
        *(extension.lower() for extension in source_extensions),
    }
    highest = 0
    # Scan the whole archledger directory tree so that section files are
    # found whether they live at the legacy <archledger_dir>/sections/ location
    # or the profile-owned <archledger_dir>/profiles/arc42/sections/ location.
    if archledger_dir.is_dir():
        for path in archledger_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in known_extensions:
                continue
            try:
                number = parse_local_ref(path.stem).number
            except IdFormatError:
                continue
            highest = max(highest, number)
    return highest + 1


def next_number_floor(
    archledger_dir: Path,
    current_next_number: int,
    *,
    source_extensions: tuple[str, ...] = (),
) -> int:
    return max(
        current_next_number,
        recompute_next_number(
            archledger_dir,
            source_extensions=source_extensions,
        ),
    )
