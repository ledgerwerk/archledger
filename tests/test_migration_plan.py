"""Tests for archledger migrate plan command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _json_result(result) -> dict:
    """Parse JSON output from CLI result."""
    return json.loads(result.stdout)


def _legacy_project(root: Path) -> None:
    """Create a minimal legacy project."""
    config = root / ".archledger.toml"
    config.write_text(
        'config_version = 10\narchledger_dir = ".archledger"\n'
        'project_uuid = "12345678-1234-1234-1234-123456789abc"\n'
        'project_name = "Test"\n'
        '\n[ledger]\ncode = "al"\nname = "archledger"\n'
        '\n[source]\nformat = "markdown"\nfront_matter = "yaml"\n'
        'section_extension = ".md"\nrecord_extension = ".md"\nschema_version = 4\n'
        '\n[profiles]\nenabled = ["arc42"]\ndefault = "arc42"\n'
        '\n[profiles.arc42]\nsections_dir = "profiles/arc42/sections"\n'
    )
    data = root / ".archledger"
    (data / "sections").mkdir(parents=True)
    (data / "storage.yaml").write_text(
        "uuid: 12345678-1234-1234-1234-123456789abc\nversion: 0.3.0\nnext_number: 2\n"
    )
    (data / "sections/content-0001.md").write_text(
        "---\nid: content-0001\n---\n# Test\n"
    )


def test_migrate_plan_project_layout_exists(tmp_path: Path) -> None:
    """migrate plan project-layout command must exist."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    assert result.exit_code != 2


def test_migrate_plan_is_read_only(tmp_path: Path) -> None:
    """Plan command must not modify any files."""
    _legacy_project(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )

    after = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after


def test_migrate_plan_has_schema(tmp_path: Path) -> None:
    """Plan must have archledger.migration-plan.v1 schema."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    assert payload["ok"] is True
    plan = payload["result"]
    assert plan.get("schema") == "archledger.migration-plan.v1"


def test_migrate_plan_has_plan_hash(tmp_path: Path) -> None:
    """Plan must have a stable plan_hash."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    plan = payload["result"]
    assert "plan_hash" in plan
    assert plan["plan_hash"].startswith("sha256:")


def test_migrate_plan_deterministic(tmp_path: Path) -> None:
    """Repeated plans must be byte-identical."""
    _legacy_project(tmp_path)

    result1 = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    result2 = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )

    assert result1.stdout == result2.stdout


def test_migrate_plan_has_source_fingerprint(tmp_path: Path) -> None:
    """Plan must include a source fingerprint."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    plan = payload["result"]
    assert "source" in plan
    assert "fingerprint" in plan["source"]
    assert plan["source"]["fingerprint"].startswith("sha256:")


def test_migrate_plan_output_file_matches_result(tmp_path: Path) -> None:
    """--output file content must match the returned plan."""
    _legacy_project(tmp_path)
    output_file = tmp_path / "plan.json"

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "migrate",
            "plan",
            "project-layout",
            "--output",
            str(output_file),
        ],
    )
    payload = _json_result(result)

    assert output_file.exists()
    file_content = json.loads(output_file.read_text())
    assert file_content == payload["result"]
