"""Tests for the unified read-only root command contract."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _payload(result) -> dict:
    return json.loads(result.stdout)


def test_commands_and_nested_help_are_inventory_driven() -> None:
    commands = runner.invoke(app, ["--json", "commands"])
    assert commands.exit_code == 0
    payload = _payload(commands)
    assert payload["result"]["commands"]
    assert any(
        item["path"] == "migrate status" for item in payload["result"]["commands"]
    )

    help_result = runner.invoke(app, ["--json", "help", "migrate", "status"])
    assert help_result.exit_code == 0
    help_payload = _payload(help_result)
    assert help_payload["result"]["command"]["path"] == "migrate status"


def test_root_status_and_next_action_are_zero_for_uninitialized(tmp_path: Path) -> None:
    status = runner.invoke(app, ["--root", str(tmp_path), "--json", "status"])
    assert status.exit_code == 0
    status_payload = _payload(status)
    assert status_payload["result"]["state"] == "uninitialized"
    assert status_payload["result"]["recommended_next"] == "archledger init"

    next_action = runner.invoke(app, ["--root", str(tmp_path), "--json", "next-action"])
    assert next_action.exit_code == 0
    assert _payload(next_action)["result"]["recommended_next"] == "archledger init"


def test_info_and_doctor_are_read_only_for_uninitialized(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    info = runner.invoke(app, ["--root", str(tmp_path), "--json", "info"])
    doctor = runner.invoke(app, ["--root", str(tmp_path), "--json", "doctor"])
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert info.exit_code == 0
    assert doctor.exit_code == 0
    assert _payload(info)["result"]["state"] == "uninitialized"
    assert _payload(doctor)["result"]["errors"] == []
    assert before == after
