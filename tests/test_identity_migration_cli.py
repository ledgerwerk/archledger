from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_new_record_uses_local_identity_and_ref(tmp_path: Path) -> None:
    init = runner.invoke(
        app, ["--root", str(tmp_path), "init", "--source-format", "markdown"]
    )
    assert init.exit_code == 0, init.stdout

    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "adr", "Use ledgercore IDs"],
    )
    assert created.exit_code == 0, created.stdout
    payload = json.loads(created.stdout)["result"]
    assert payload["id"] == "adr-0013"
    assert payload["kind"] == "adr"
    assert payload["ref"] == "al:adr-0013"
    assert payload["path"].endswith("records/decisions/adr-0013.md")

    created_file = tmp_path / ".archledger" / "records" / "decisions" / "adr-0013.md"
    assert created_file.is_file()
    text = created_file.read_text(encoding="utf-8")
    assert "id: adr-0013" in text
    assert "kind: adr" in text
    assert "type: adr" in text


def test_migrate_ids_converts_legacy_segmented_record(tmp_path: Path) -> None:
    init = runner.invoke(
        app, ["--root", str(tmp_path), "init", "--source-format", "markdown"]
    )
    assert init.exit_code == 0, init.stdout

    old_file = tmp_path / ".archledger" / "records" / "decisions" / "adr-0013.md"
    old_file.write_text(
        "\n".join(
            [
                "---",
                "schema_version: 2",
                "id: adr-0013",
                "type: adr",
                "title: Legacy ADR",
                "status: accepted",
                "section: architecture_decisions",
                "order: 10",
                "---",
                "",
                "Legacy body",
                "",
            ]
        ),
        encoding="utf-8",
    )
    new_file = tmp_path / ".archledger" / "records" / "decisions" / "adr-0013.md"
    if new_file.exists():
        new_file.unlink()

    migrated = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "ids",
            "--to",
            "ledgercore",
            "--apply",
        ],
    )
    assert migrated.exit_code == 0, migrated.stdout
    payload = json.loads(migrated.stdout)["result"]
    assert payload["migrated_count"] >= 1
    assert new_file.is_file()
    migrated_text = new_file.read_text(encoding="utf-8")
    assert "id: adr-0013" in migrated_text
    assert "kind: adr" in migrated_text


def test_read_json_exposes_kind_and_ref(tmp_path: Path) -> None:
    init = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert init.exit_code == 0, init.stdout
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "CLI", "--status", "accepted"],
    )
    assert created.exit_code == 0, created.stdout

    read = runner.invoke(app, ["--root", str(tmp_path), "--json", "read"])
    assert read.exit_code == 0, read.stdout
    records = json.loads(read.stdout)["result"]["records"]
    assert any(
        item["kind"] == "block" and item["ref"] == f"al:{item['id']}"
        for item in records
    )
