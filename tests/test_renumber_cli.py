"""Regression tests for the deprecated renumber command.

``renumber`` is a legacy command that operates on the old prefix-based ID
format (``al_0001`` / ``al_<segment>_0001``).  Current projects create
ledgercore local IDs (``content-0001``, ``adr-0001``, etc.) and should use
``migrate ids`` instead.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def init_project(tmp_path: Path, *, source_format: str = "asciidoc") -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", source_format],
    )
    assert result.exit_code == 0, result.stdout


def test_renumber_rejects_current_ledgercore_ids(tmp_path: Path) -> None:
    """renumber must fail with a clear legacy/deprecated message on a project
    that uses current ledgercore local IDs."""
    init_project(tmp_path, source_format="markdown")
    created = runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])
    assert created.exit_code == 0

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "renumber", "--apply"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    message = payload["error"]["message"].lower()
    assert "legacy" in message
    assert "migrate ids" in payload["error"]["message"]
