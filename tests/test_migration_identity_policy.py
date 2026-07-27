"""Tests for archledger migration identity policy."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _json_result(result) -> dict:
    """Parse JSON output from CLI result."""
    return json.loads(result.stdout)


def _legacy_project_with_uuid(root: Path, uuid: str) -> None:
    """Create a legacy project with specific UUID."""
    config = root / ".archledger.toml"
    config.write_text(
        f'config_version = 10\narchledger_dir = ".archledger"\n'
        f'project_uuid = "{uuid}"\n'
        f'project_name = "Test"\n'
        f'\n[ledger]\ncode = "al"\nname = "archledger"\n'
        f'\n[source]\nformat = "markdown"\nfront_matter = "yaml"\n'
        f'section_extension = ".md"\nrecord_extension = ".md"\nschema_version = 4\n'
        f'\n[profiles]\nenabled = ["arc42"]\ndefault = "arc42"\n'
        f'\n[profiles.arc42]\nsections_dir = "profiles/arc42/sections"\n'
    )
    data = root / ".archledger"
    (data / "sections").mkdir(parents=True)
    (data / "storage.yaml").write_text(
        f"uuid: {uuid}\nversion: 0.3.0\nnext_number: 2\n"
    )
    (data / "sections/content-0001.md").write_text(
        "---\nid: content-0001\n---\n# Test\n"
    )


def _shared_manifest(root: Path, manifest_uuid: str) -> None:
    """Create a shared manifest with different UUID."""
    ledger = root / ".ledger"
    ledger.mkdir()
    (ledger / "ledger.toml").write_text(
        f'schema_version = 3\n\n[project]\nuuid = "{manifest_uuid}"\nname = "Shared"\n'
    )


def test_uuid_mismatch_blocks_plan(tmp_path: Path) -> None:
    """UUID mismatch must block plan with remediation."""
    legacy_uuid = "11111111-1111-1111-1111-111111111111"
    manifest_uuid = "22222222-2222-2222-2222-222222222222"

    _legacy_project_with_uuid(tmp_path, legacy_uuid)
    _shared_manifest(tmp_path, manifest_uuid)

    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    assert payload["ok"] is False
    assert "project_uuid_mismatch" in str(payload.get("error", {}))
    assert "adopt-project" in str(payload.get("error", {}).get("remediation", []))


def test_uuid_mismatch_with_adopt_project(tmp_path: Path) -> None:
    """--identity-policy adopt-project must allow UUID adoption."""
    legacy_uuid = "11111111-1111-1111-1111-111111111111"
    manifest_uuid = "22222222-2222-2222-2222-222222222222"

    _legacy_project_with_uuid(tmp_path, legacy_uuid)
    _shared_manifest(tmp_path, manifest_uuid)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "plan",
            "project-layout",
            "--identity-policy",
            "adopt-project",
        ],
    )
    payload = _json_result(result)
    assert payload["ok"] is True
    plan = payload["result"]
    assert plan["project"]["identity_policy"] == "adopt-project"
    assert plan["project"]["target_uuid"] == manifest_uuid


def test_matching_uuid_proceeds(tmp_path: Path) -> None:
    """Matching UUID must proceed without adopt-project."""
    uuid = "12345678-1234-1234-1234-123456789abc"

    _legacy_project_with_uuid(tmp_path, uuid)
    _shared_manifest(tmp_path, uuid)

    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    assert payload["ok"] is True


def test_no_manifest_creates_new(tmp_path: Path) -> None:
    """No manifest must create new one with legacy UUID."""
    uuid = "12345678-1234-1234-1234-123456789abc"
    _legacy_project_with_uuid(tmp_path, uuid)

    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    assert payload["ok"] is True
    plan = payload["result"]
    assert plan["project"]["target_uuid"] == uuid
