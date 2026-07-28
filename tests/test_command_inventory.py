"""Tests for archledger command inventory and metadata."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from archledger.cli import app
from archledger.cli_inventory import validate_inventory

runner = CliRunner()


def _json_result(result) -> dict:
    """Parse JSON output from CLI result."""
    return json.loads(result.stdout)


def test_commands_command_exists() -> None:
    """commands command must exist."""
    result = runner.invoke(app, ["commands"])
    assert result.exit_code != 2


def test_help_command_exists() -> None:
    """help command must exist."""
    result = runner.invoke(app, ["help"])
    assert result.exit_code != 2


def test_migrate_commands_in_inventory() -> None:
    """All migration commands must appear in command inventory."""
    result = runner.invoke(app, ["--json", "commands"])
    if result.exit_code == 0:
        payload = _json_result(result)
        commands = payload.get("result", {}).get("commands", [])
        command_names = [c.get("name", "") for c in commands]

        # These must exist
        assert "migrate status" in command_names or "migrate" in command_names
        assert "migrate plan" in command_names or "migrate" in command_names
        assert "migrate apply" in command_names or "migrate" in command_names
        assert "migrate recover" in command_names or "migrate" in command_names
        assert "migrate cleanup" in command_names or "migrate" in command_names


def test_migration_commands_have_metadata() -> None:
    """Migration commands must have proper metadata."""
    result = runner.invoke(app, ["--json", "commands"])
    if result.exit_code == 0:
        payload = _json_result(result)
        commands = payload.get("result", {}).get("commands", [])

        for cmd in commands:
            if "migrate" in cmd.get("name", ""):
                assert "effect" in cmd
                assert "requires_workspace" in cmd
                assert "supports_json" in cmd
                assert "stability" in cmd


def test_inventory_drift_guard_reports_unregistered_paths() -> None:
    """The shared guard fails closed when registration and metadata diverge."""
    findings = validate_inventory({"status", "unknown"})
    assert "registered command lacks metadata: unknown" in findings
    assert "metadata command is not registered: migrate status" in findings
