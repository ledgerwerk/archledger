"""Tests for bdd metadata warnings in archledger check."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)

runner = CliRunner()


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout


def test_check_succeeds_on_records_without_bdd_metadata(tmp_path: Path) -> None:
    """ac-0005: check is clean on projects without bdd metadata."""
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "Hello"],
    )
    assert result.exit_code == 0, result.stdout
    check = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])
    assert check.exit_code == 0, check.stdout
    payload = json.loads(check.stdout)
    # No BDD-related errors or warnings on records without bdd metadata
    assert not any(
        "bdd" in w.get("message", "").lower() for w in payload["result"]["errors"]
    )
    assert not any(
        "bdd" in w.get("message", "").lower() for w in payload["result"]["warnings"]
    )


def test_check_warns_on_malformed_bdd_metadata(tmp_path: Path) -> None:
    """ac-0005: check warns when a record has malformed bdd metadata."""
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "runtime_scenario",
            "Hello",
            "--status",
            "proposed",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])

    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"] = "not-a-mapping"  # malformed
    write_front_matter_document(record_path, metadata, body)

    check = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])
    payload = json.loads(check.stdout)
    assert any("bdd" in w.get("message", "") for w in payload["result"]["warnings"])


def test_check_succeeds_on_valid_bdd_metadata(tmp_path: Path) -> None:
    """ac-0005: check passes cleanly on a record with valid bdd metadata."""
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "runtime_scenario",
            "Hello",
            "--status",
            "proposed",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])

    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"] = {
        "feature": "F",
        "scenario": "S",
        "given": ["g"],
        "when": ["w"],
        "then": ["t"],
    }
    write_front_matter_document(record_path, metadata, body)

    check = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])
    assert check.exit_code == 0, check.stdout
    payload = json.loads(check.stdout)
    # No BDD-related errors or warnings in check result
    assert not any(
        "bdd" in w.get("message", "").lower() for w in payload["result"]["errors"]
    )
    assert not any(
        "bdd" in w.get("message", "").lower() for w in payload["result"]["warnings"]
    )
