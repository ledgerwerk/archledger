from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

from archledger.errors import StorageError
from archledger.model import (
    RECORD_TYPE_TO_DIR,
    RECORD_TYPE_TO_FILENAME_PREFIX,
    VALID_RECORD_TYPES,
)
from archledger.storage.common import read_text, utc_now_iso, write_text


@dataclass(frozen=True, slots=True)
class StorageMeta:
    storage_version: int
    created_with_archledger: str
    project_uuid: str
    created_at: str
    next_numbers: dict[str, int]


def default_storage_meta(project_uuid: str, archledger_version: str) -> StorageMeta:
    return StorageMeta(
        storage_version=1,
        created_with_archledger=archledger_version,
        project_uuid=project_uuid,
        created_at=utc_now_iso(),
        next_numbers={counter_key: 1 for counter_key in _counter_keys()},
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

    next_numbers = raw_data.get("next_numbers")
    if not isinstance(next_numbers, dict):
        raise StorageError("storage.yaml next_numbers must be a mapping.")

    normalized_next_numbers: dict[str, int] = {}
    for key in _counter_keys():
        value = next_numbers.get(key, 1)
        if not isinstance(value, int) or value < 1:
            raise StorageError(
                f"storage.yaml next_numbers[{key!r}] must be a positive integer."
            )
        normalized_next_numbers[key] = value

    storage_version = raw_data.get("storage_version")
    created_with_archledger = raw_data.get("created_with_archledger")
    project_uuid = raw_data.get("project_uuid")
    created_at = raw_data.get("created_at")
    if storage_version != 1:
        raise StorageError("storage_version must be 1.")
    if not all(
        isinstance(value, str) and value
        for value in (created_with_archledger, project_uuid, created_at)
    ):
        raise StorageError(
            "storage.yaml created_with_archledger, project_uuid, and created_at "
            "must be non-empty strings."
        )

    return StorageMeta(
        storage_version=1,
        created_with_archledger=cast(str, created_with_archledger),
        project_uuid=cast(str, project_uuid),
        created_at=cast(str, created_at),
        next_numbers=normalized_next_numbers,
    )


def write_storage_meta(path: Path, meta: StorageMeta) -> None:
    content = yaml.safe_dump(
        {
            "storage_version": meta.storage_version,
            "created_with_archledger": meta.created_with_archledger,
            "project_uuid": meta.project_uuid,
            "created_at": meta.created_at,
            "next_numbers": meta.next_numbers,
        },
        sort_keys=False,
    )
    write_text(path, content)


def recompute_next_numbers(records_dir: Path) -> dict[str, int]:
    next_numbers = {counter_key: 1 for counter_key in _counter_keys()}
    for record_type in VALID_RECORD_TYPES:
        directory = records_dir / RECORD_TYPE_TO_DIR[record_type]
        prefix = RECORD_TYPE_TO_FILENAME_PREFIX[record_type]
        pattern = re.compile(
            
                rf"^{re.escape(prefix)}_?(?P<number>\d{{4}})$"
                if prefix == "adr"
                else rf"^{re.escape(prefix)}_(?P<number>\d{{4}})$"
            
        )
        if not directory.is_dir():
            continue
        highest = 0
        for path in directory.glob("*.md"):
            match = pattern.match(path.stem)
            if match is None:
                continue
            highest = max(highest, int(match.group("number")))
        next_numbers[prefix] = highest + 1
    return next_numbers


def _counter_keys() -> tuple[str, ...]:
    return tuple(dict.fromkeys(RECORD_TYPE_TO_FILENAME_PREFIX.values()))
