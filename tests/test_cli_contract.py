"""Tests for archledger CLI contract (JSON envelope, exit codes)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _json_result(result) -> dict:
    """Parse JSON output from CLI result."""
    return json.loads(result.stdout)


def test_json_envelope_has_required_fields(tmp_path: Path) -> None:
    """JSON output must have all ledgerwerk.cli.v1 fields."""
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
    assert "result" in payload
    assert "events" in payload
    assert "warnings" in payload


def test_json_error_has_code_and_remediation(tmp_path: Path) -> None:
    """Error responses must have code and remediation."""
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "apply",
            "project-layout",
            "--reason",
            "test",
        ],
    )
    payload = _json_result(result)
    assert payload["ok"] is False
    assert "error" in payload
    error = payload["error"]
    assert "code" in error
    assert "message" in error
    assert "remediation" in error


def test_exit_code_0_for_success(tmp_path: Path) -> None:
    """Successful commands must exit with code 0."""
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "status"]
    )
    assert result.exit_code == 0


def test_exit_code_4_for_stale_plan(tmp_path: Path) -> None:
    """Stale plans must exit with code 4."""
    # This will fail until we implement plan validation
    plan_file = tmp_path / "stale.json"
    plan_file.write_text(
        '{"schema": "archledger.migration-plan.v1", "plan_hash": "sha256:wrong"}'
    )

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "apply",
            "project-layout",
            "--plan-file",
            str(plan_file),
            "--reason",
            "test",
        ],
    )
    assert result.exit_code == 4
