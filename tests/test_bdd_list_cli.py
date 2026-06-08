"""Tests for archledger bdd list CLI command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout


def test_bdd_list_automation_rejects_unknown_status(tmp_path: Path) -> None:
    """P2: bdd list --automation rejects unknown status with a JSON error envelope."""
    _init(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "list",
            "--automation",
            "banana",
        ],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "banana" in payload["error"]["message"]
    assert "automated" in payload["error"]["message"]


def test_bdd_list_automation_accepts_known_status(tmp_path: Path) -> None:
    """A known automation status does not error (may return an empty list)."""
    _init(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "list",
            "--automation",
            "automated",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
