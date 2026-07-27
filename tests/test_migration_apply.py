"""Tests for archledger migrate apply command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _json_result(result) -> dict:
    """Parse JSON output from CLI result."""
    return json.loads(result.stdout)


def _legacy_project(
    root: Path, uuid: str = "12345678-1234-1234-1234-123456789abc"
) -> None:
    """Create a minimal legacy project."""
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
        f"storage_version: 3\ncreated_with_archledger: 0.3.0\n"
        f"project_uuid: {uuid}\nversion: 1\nnext_number: 2\n"
    )
    (data / "sections/content-0001.md").write_text(
        "---\nid: content-0001\n---\n# Test\n"
    )


def test_migrate_apply_requires_reason(tmp_path: Path) -> None:
    """Apply must require --reason."""
    _legacy_project(tmp_path)
    # First get a plan
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    plan = payload["result"]

    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))

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
        ],
    )
    assert result.exit_code != 0


def test_migrate_apply_validates_plan_file(tmp_path: Path) -> None:
    """Apply must validate the plan file."""
    _legacy_project(tmp_path)

    plan_file = tmp_path / "plan.json"
    plan_file.write_text('{"schema": "wrong-schema"}')

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
    assert result.exit_code != 0


def test_migrate_apply_preserves_source(tmp_path: Path) -> None:
    """Apply must preserve the legacy source."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    plan = payload["result"]
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))

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
            "test migration",
        ],
    )
    payload = _json_result(result)
    assert payload["ok"] is True

    # Legacy source should still exist
    assert (tmp_path / ".archledger.toml").exists()
    assert (tmp_path / ".archledger").is_dir()
    assert (tmp_path / ".archledger/sections/content-0001.md").exists()


def test_migrate_apply_no_staging_residue(tmp_path: Path) -> None:
    """Apply must not leave staging directories."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    plan = payload["result"]
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))

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
            "test migration",
        ],
    )

    # Check no .migration directory exists
    ledger = tmp_path / ".ledger"
    arch = ledger / "archledger"
    if arch.exists():
        migration_dirs = list(arch.glob(".migration*"))
        assert len(migration_dirs) == 0, f"Staging residue found: {migration_dirs}"


def test_migrate_apply_receipt_paths_are_canonical(tmp_path: Path) -> None:
    """Receipt paths must be final canonical paths, not staging paths."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    plan = payload["result"]
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))

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
            "test migration",
        ],
    )
    payload = _json_result(result)
    assert payload["ok"] is True

    # Check receipt
    receipt_path = payload["result"].get("receipt_path")
    assert receipt_path is not None
    assert ".migration" not in str(receipt_path)


def test_migrate_apply_dry_run(tmp_path: Path) -> None:
    """Apply with --dry-run must not modify files."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "plan", "project-layout"]
    )
    payload = _json_result(result)
    plan = payload["result"]
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))

    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

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
            "--dry-run",
            "--reason",
            "test dry run",
        ],
    )
    assert result.exit_code == 0

    after = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after
