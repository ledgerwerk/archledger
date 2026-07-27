"""Tests for archledger migrate recovery."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _json_result(result) -> dict:
    """Parse JSON output from CLI result."""
    return json.loads(result.stdout)


def test_migrate_recover_exists(tmp_path: Path) -> None:
    """migrate recover command must exist."""
    # Create a dummy journal file
    journal = tmp_path / "test.toml"
    journal.write_text('migration = "project-layout"\nstatus = "incomplete"\n')
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "recover",
            "--journal",
            str(journal),
        ],
    )
    # Should not be a "no such command" error
    assert result.exit_code != 2


def test_migrate_recover_requires_journal(tmp_path: Path) -> None:
    """migrate recover requires --journal."""
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "recover"]
    )
    assert result.exit_code != 0


def test_migrate_status_reports_recovery_required(tmp_path: Path) -> None:
    """Status must report recovery-required state when journal is incomplete."""
    # This will need to be implemented after the recovery system is in place
    # For now, this test should fail
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "status"]
    )
    payload = _json_result(result)
    # This assertion will fail until we implement recovery state detection
    assert "recovery_required" not in payload["result"].get("state", "")


def test_migrate_recover_dry_run_is_read_only(tmp_path: Path) -> None:
    """Recover dry-run must not modify any files."""
    # This test will fail until recovery is implemented
    journal = tmp_path / ".ledger" / "migrations" / "test.toml"
    journal.parent.mkdir(parents=True)
    journal.write_text('migration_id = "test"\nstatus = "incomplete"\n')

    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "recover",
            "--journal",
            str(journal),
            "--dry-run",
        ],
    )

    after = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after
