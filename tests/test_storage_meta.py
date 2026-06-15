from __future__ import annotations

from pathlib import Path

import pytest

from archledger.errors import StorageError
from archledger.storage.meta import (
    StorageMeta,
    next_number_floor,
    read_storage_meta,
    write_storage_meta,
)


def test_storage_next_number_bool_is_rejected(tmp_path: Path) -> None:
    storage = tmp_path / "storage.yaml"
    storage.write_text(
        "\n".join(
            [
                "storage_version: 2",
                'created_with_archledger: "0.1.dev10"',
                'project_uuid: "00000000-0000-4000-8000-000000000000"',
                'created_at: "2026-05-20T00:00:00Z"',
                "next_number: true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(StorageError, match="next_number"):
        read_storage_meta(storage)


def test_storage_version_must_be_supported(tmp_path: Path) -> None:
    storage = tmp_path / "storage.yaml"
    storage.write_text(
        "\n".join(
            [
                "storage_version: 1",
                'created_with_archledger: "0.1.dev10"',
                'project_uuid: "00000000-0000-4000-8000-000000000000"',
                'created_at: "2026-05-20T00:00:00Z"',
                "next_number: 13",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(StorageError, match="storage_version"):
        read_storage_meta(storage)


def test_legacy_v2_storage_defaults_version_to_one(tmp_path: Path) -> None:
    storage = tmp_path / "storage.yaml"
    storage.write_text(
        "\n".join(
            [
                "storage_version: 2",
                'created_with_archledger: "0.1.dev10"',
                'project_uuid: "00000000-0000-4000-8000-000000000000"',
                'created_at: "2026-05-20T00:00:00Z"',
                "next_number: 13",
                "",
            ]
        ),
        encoding="utf-8",
    )

    meta = read_storage_meta(storage)

    assert meta.storage_version == 2
    assert meta.version == 1


def test_v3_writer_emits_version_without_timestamp(tmp_path: Path) -> None:
    storage = tmp_path / "storage.yaml"

    write_storage_meta(
        storage,
        StorageMeta(
            storage_version=3,
            created_with_archledger="0.1.dev10",
            project_uuid="00000000-0000-4000-8000-000000000000",
            version=4,
            next_number=13,
        ),
    )

    text = storage.read_text(encoding="utf-8")
    assert "storage_version: 3" in text
    assert "version: 4" in text
    assert "created_at:" not in text


def test_next_number_floor_preserves_counter_floor(tmp_path: Path) -> None:
    archledger_dir = tmp_path / ".archledger"
    sections = archledger_dir / "sections"
    sections.mkdir(parents=True)
    (sections / "al_0001.adoc").write_text("---\n---\n", encoding="utf-8")

    assert next_number_floor(archledger_dir, 50) == 50
