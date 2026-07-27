"""Tests for archledger migrate status command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _json_result(result) -> dict:
    """Parse JSON output from CLI result."""
    return json.loads(result.stdout)


def test_migrate_status_exists(tmp_path: Path) -> None:
    """migrate status command must exist."""
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "status"]
    )
    # Should not be a "no such command" error
    assert result.exit_code != 2


def test_migrate_status_empty_directory(tmp_path: Path) -> None:
    """Empty directory should report uninitialized state."""
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "status"]
    )
    payload = _json_result(result)
    assert payload["ok"] is True
    assert payload["result"]["state"] == "uninitialized"


def test_migrate_status_legacy_directory(tmp_path: Path) -> None:
    """Legacy .archledger directory should report legacy state."""
    config = tmp_path / ".archledger.toml"
    config.write_text(
        'config_version = 10\narchledger_dir = ".archledger"\n'
        'project_uuid = "12345678-1234-1234-1234-123456789abc"\n'
        'project_name = "Test"\n'
    )
    data = tmp_path / ".archledger"
    data.mkdir()
    (data / "storage.yaml").write_text(
        "uuid: 12345678-1234-1234-1234-123456789abc\nversion: 0.3.0\n"
    )

    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "status"]
    )
    payload = _json_result(result)
    assert payload["ok"] is True
    assert payload["result"]["state"] == "legacy"
    assert "project-layout" in payload["result"].get("available_migrations", [])


def test_migrate_status_canonical_directory(tmp_path: Path) -> None:
    """Canonical .ledger directory should report canonical state."""
    ledger = tmp_path / ".ledger"
    ledger.mkdir()
    (ledger / "ledger.toml").write_text(
        "schema_version = 3\n\n[project]\n"
        'uuid = "12345678-1234-1234-1234-123456789abc"\nname = "Test"\n'
    )
    arch = ledger / "archledger"
    arch.mkdir()
    (arch / "config.toml").write_text("config_version = 12\n")
    (arch / "data").mkdir()

    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "status"]
    )
    payload = _json_result(result)
    assert payload["ok"] is True
    assert payload["result"]["state"] in ("canonical", "canonical-ready", "clean")


def test_migrate_status_json_schema(tmp_path: Path) -> None:
    """JSON output must use ledgerwerk.cli.v1 schema."""
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "status"]
    )
    payload = _json_result(result)
    assert "schema" in payload
    assert payload["schema"] == "ledgerwerk.cli.v1"
    assert "ok" in payload
    assert "tool" in payload
    assert payload["tool"] == "archledger"
    assert "command" in payload
    assert "events" in payload
    assert "warnings" in payload
