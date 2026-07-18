from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)
from archledger.storage.paths import resolve_project_paths

runner = CliRunner()


def test_metadata_migration_dry_run_apply_and_idempotence(tmp_path: Path) -> None:
    assert (
        runner.invoke(
            app, ["--root", str(tmp_path), "init", "--source-format", "markdown"]
        ).exit_code
        == 0
    )
    paths, config, warnings = resolve_project_paths(tmp_path)
    assert not warnings
    section = paths.sections_dir / "content-0001.md"
    for section_path in paths.sections_dir.glob(f"*{config.section_extension}"):
        metadata, _ = read_front_matter_document(section_path)
        write_front_matter_document(
            section_path, metadata, "Authored architecture prose for migration.\n"
        )
    section.write_text(
        section.read_text(encoding="utf-8")
        .replace("schema_version: 4", "schema_version: 3")
        .replace(
            "version: 1",
            'date: "2026-01-01"\ncreated_at: "2026-01-01T00:00:00Z"',
        ),
        encoding="utf-8",
    )
    config_path = paths.config_path
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "schema_version = 4", "schema_version = 3"
        ),
        encoding="utf-8",
    )
    storage_path = paths.storage_meta_path
    storage_path.write_text(
        storage_path.read_text(encoding="utf-8")
        .replace("storage_version: 3", "storage_version: 2")
        .replace("version: 1", 'created_at: "2026-01-01T00:00:00Z"'),
        encoding="utf-8",
    )
    assert (
        runner.invoke(app, ["--root", str(tmp_path), "source", "snapshot"]).exit_code
        == 0
    )
    source_state_path = paths.source_state_path
    source_state = json.loads(source_state_path.read_text(encoding="utf-8"))
    source_state["schema"] = "archledger.source-state.v2"
    source_state.pop("version")
    source_state["created_at"] = "2026-01-01T00:00:00Z"
    source_state["updated_at"] = "2026-01-01T00:00:00Z"
    source_state_path.write_text(json.dumps(source_state), encoding="utf-8")

    dry_run = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "migrate", "metadata"],
    )

    assert dry_run.exit_code == 0
    dry_payload = json.loads(dry_run.stdout)["result"]
    assert dry_payload["apply"] is False
    assert dry_payload["records_changed"] == 1
    assert "created_at:" in section.read_text(encoding="utf-8")

    applied = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "metadata",
            "--apply",
        ],
    )

    assert applied.exit_code == 0
    section_text = section.read_text(encoding="utf-8")
    assert "schema_version: 4" in section_text
    assert "version: 1" in section_text
    assert "date:" not in section_text
    assert "created_at:" not in section_text
    assert "config_version = 12" in config_path.read_text(encoding="utf-8")
    assert "schema_version = 4" in config_path.read_text(encoding="utf-8")
    storage_text = storage_path.read_text(encoding="utf-8")
    assert "storage_version: 3" in storage_text
    assert "version: 1" in storage_text
    assert "created_at:" not in storage_text
    migrated_state = json.loads(source_state_path.read_text(encoding="utf-8"))
    assert migrated_state["schema"] == "archledger.source-state.v3"
    assert migrated_state["version"] == 1
    assert "created_at" not in migrated_state
    assert "updated_at" not in migrated_state

    strict_check = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "check", "--strict"]
    )
    assert strict_check.exit_code == 0, strict_check.stdout
    strict_payload = json.loads(strict_check.stdout)
    assert strict_payload["result"]["errors"] == []
    assert strict_payload["result"]["warnings"] == []

    repeated = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "metadata",
            "--apply",
        ],
    )
    repeated_payload = json.loads(repeated.stdout)["result"]
    assert repeated.exit_code == 0
    assert repeated_payload["records_changed"] == 0
    assert repeated_payload["storage_changed"] is False
    assert repeated_payload["source_state_changed"] is False
    assert repeated_payload["config_changed"] is False
