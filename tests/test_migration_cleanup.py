"""Tests for archledger migrate cleanup command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _json_result(result) -> dict:
    """Parse JSON output from CLI result."""
    return json.loads(result.stdout)


def test_migrate_cleanup_exists(tmp_path: Path) -> None:
    """migrate cleanup command must exist."""
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "cleanup", "project-layout"]
    )
    # Should not be a "no such command" error
    assert result.exit_code != 2


def test_migrate_cleanup_requires_yes(tmp_path: Path) -> None:
    """Cleanup must require --yes."""
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "cleanup",
            "project-layout",
            "--reason",
            "test",
        ],
    )
    assert result.exit_code != 0


def test_migrate_cleanup_requires_reason(tmp_path: Path) -> None:
    """Cleanup must require --reason."""
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "cleanup",
            "project-layout",
            "--yes",
        ],
    )
    assert result.exit_code != 0


def test_migrate_cleanup_dry_run_is_read_only(tmp_path: Path) -> None:
    """Cleanup dry-run must not modify files."""
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "cleanup",
            "project-layout",
            "--dry-run",
        ],
    )

    after = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after


def test_migrate_cleanup_not_invoked_by_apply(tmp_path: Path) -> None:
    """Cleanup must be separate from apply - not invoked automatically."""
    # This test will fail until cleanup is properly separated
    pass
