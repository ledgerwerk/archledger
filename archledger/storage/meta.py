from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

from archledger.errors import StorageError
from archledger.ids import parse_ledger_id
from archledger.model import SOURCE_FORMAT_EXTENSIONS
from archledger.storage.common import read_text, utc_now_iso, write_text_atomic


@dataclass(frozen=True, slots=True)
class StorageMeta:
    storage_version: int
    created_with_archledger: str
    project_uuid: str
    created_at: str
    next_number: int


def default_storage_meta(project_uuid: str, archledger_version: str) -> StorageMeta:
    return StorageMeta(
        storage_version=2,
        created_with_archledger=archledger_version,
        project_uuid=project_uuid,
        created_at=utc_now_iso(),
        next_number=1,
    )


def read_storage_meta(path: Path) -> StorageMeta:
    if not path.is_file():
        raise StorageError(f"Missing storage metadata file: {path}")
    try:
        raw_data = yaml.safe_load(read_text(path))
    except yaml.YAMLError as exc:
        raise StorageError(f"Failed to parse storage metadata: {path}") from exc
    if not isinstance(raw_data, dict):
        raise StorageError("storage.yaml must contain a mapping.")

    storage_version = raw_data.get("storage_version")
    created_with_archledger = raw_data.get("created_with_archledger")
    project_uuid = raw_data.get("project_uuid")
    created_at = raw_data.get("created_at")
    next_number = raw_data.get("next_number")

    if storage_version != 2:
        raise StorageError("storage_version must be 2.")
    if not all(
        isinstance(value, str) and value
        for value in (created_with_archledger, project_uuid, created_at)
    ):
        raise StorageError(
            "storage.yaml created_with_archledger, project_uuid, and created_at "
            "must be non-empty strings."
        )
    if isinstance(next_number, bool) or not isinstance(next_number, int) or next_number < 1:
        raise StorageError("storage.yaml next_number must be a positive integer.")

    return StorageMeta(
        storage_version=2,
        created_with_archledger=cast(str, created_with_archledger),
        project_uuid=cast(str, project_uuid),
        created_at=cast(str, created_at),
        next_number=next_number,
    )


def write_storage_meta(path: Path, meta: StorageMeta) -> None:
    content = yaml.safe_dump(
        {
            "storage_version": meta.storage_version,
            "created_with_archledger": meta.created_with_archledger,
            "project_uuid": meta.project_uuid,
            "created_at": meta.created_at,
            "next_number": meta.next_number,
        },
        sort_keys=False,
    )
    write_text_atomic(path, content)


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
    for root in (archledger_dir / "sections", archledger_dir / "records"):
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in known_extensions:
                continue
            try:
                number = parse_ledger_id(path.stem)
            except ValueError:
                continue
            highest = max(highest, number)
    return highest + 1
