from __future__ import annotations

from pathlib import Path
from uuid import UUID

from archledger.project_migration import (
    apply_project_migration,
    inspect_project_migration,
)
from archledger.storage.meta import default_storage_meta, write_storage_meta

UUID_TEXT = "12345678-1234-1234-1234-123456789abc"


def _legacy_project(root: Path) -> tuple[Path, Path]:
    config = root / ".archledger.toml"
    config.write_text(
        "\n".join(
            [
                "config_version = 10",
                'archledger_dir = ".archledger"',
                f'project_uuid = "{UUID_TEXT}"',
                'project_name = "Demo"',
                "",
                '[ledger]\ncode = "al"\nname = "archledger"',
                "",
                """[source]
format = "markdown"
front_matter = "yaml"
section_extension = ".md"
record_extension = ".md"
schema_version = 4""",
                "",
                '[profiles]\nenabled = ["arc42"]\ndefault = "arc42"',
                "",
                '[profiles.arc42]\nsections_dir = "profiles/arc42/sections"',
            ]
        )
    )
    data = root / ".archledger"
    (data / "records/requirements").mkdir(parents=True)
    (data / "sections").mkdir()
    write_storage_meta(data / "storage.yaml", default_storage_meta(UUID_TEXT, "0.3.0"))
    (data / "sections/content-0001.md").write_text("---\nid: content-0001\n---\n")
    return config, data


def test_project_migration_inspection_is_read_only(tmp_path: Path) -> None:
    config, data = _legacy_project(tmp_path)
    before = {path: path.read_bytes() for path in (config, data / "storage.yaml")}

    inspection = inspect_project_migration(tmp_path)

    assert inspection.ready
    assert inspection.source_data_root == data.resolve()
    assert inspection.source_kind == "legacy-hidden-config"
    assert inspection.source_project_uuid == UUID_TEXT
    assert inspection.section_count == 1
    assert {path: path.read_bytes() for path in before} == before
    assert not (tmp_path / ".ledger").exists()


def test_project_migration_apply_preserves_source_and_writes_receipt(
    tmp_path: Path,
) -> None:
    _, data = _legacy_project(tmp_path)
    original_storage = (data / "storage.yaml").read_bytes()
    inspection = inspect_project_migration(tmp_path)

    result = apply_project_migration(inspection)

    assert result.receipt_path.is_file()
    assert (tmp_path / ".ledger/ledger.toml").is_file()
    assert (tmp_path / ".ledger/archledger/config.toml").is_file()
    assert (
        tmp_path / ".ledger/archledger/data/storage.yaml"
    ).read_bytes() == original_storage
    assert data.is_dir()
    assert (
        tmp_path / ".ledger/archledger/data/profiles/arc42/sections/content-0001.md"
    ).is_file()
    assert (
        not (tmp_path / ".ledger/archledger/config.toml").read_text().find("archledger_dir")
        >= 0
    )
    assert UUID(
        (tmp_path / ".ledger/ledger.toml")
        .read_text()
        .split('uuid = "')[1]
        .split('"')[0]
    ) == UUID(UUID_TEXT)
