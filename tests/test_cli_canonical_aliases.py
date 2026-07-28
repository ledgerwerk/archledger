"""Canonical resource command and compatibility alias coverage."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _json(result) -> dict:
    return json.loads(result.stdout)


def _init(root: Path) -> None:
    result = runner.invoke(app, ["--root", str(root), "init"])
    assert result.exit_code == 0, result.output


def test_canonical_record_commands_and_aliases_share_services(tmp_path: Path) -> None:
    _init(tmp_path)
    canonical = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "record", "create", "adr", "Canonical"],
    )
    assert canonical.exit_code == 0, canonical.output
    record_id = _json(canonical)["result"]["id"]

    legacy = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "adr", "Legacy"],
    )
    assert legacy.exit_code == 0, legacy.output
    assert _json(legacy)["warnings"][0]["code"] == "deprecated_command"
    assert _json(legacy)["warnings"][0]["replacement"] == "record create"

    listed = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "record", "list", "--all-statuses"]
    )
    assert listed.exit_code == 0
    assert {item["id"] for item in _json(listed)["result"]["records"]} >= {record_id}

    updated = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "set-status",
            record_id,
            "proposed",
            "--reason",
            "canonical alias test",
        ],
    )
    assert updated.exit_code == 0, updated.output
    assert _json(updated)["result"]["status"] == "proposed"


def test_canonical_ref_link_and_archive_paths_work(tmp_path: Path) -> None:
    _init(tmp_path)
    first = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "record", "create", "adr", "First"],
    )
    second = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "record", "create", "adr", "Second"],
    )
    first_id = _json(first)["result"]["id"]
    second_id = _json(second)["result"]["id"]

    ref = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "ref",
            "add",
            first_id,
            "--path",
            "src/app.py",
            "--role",
            "implements",
        ],
    )
    link = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "link",
            "add",
            first_id,
            "--rel",
            "refines",
            "--target",
            second_id,
        ],
    )
    archived = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "archive",
            second_id,
            "--reason",
            "canonical archive test",
        ],
    )
    assert ref.exit_code == 0, ref.output
    assert link.exit_code == 0, link.output
    assert archived.exit_code == 0, archived.output
