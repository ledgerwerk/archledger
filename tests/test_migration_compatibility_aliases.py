"""Tests for archledger migration compatibility aliases."""

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
        "storage_version: 3\n"
        "created_with_archledger: 0.3.0\n"
        "project_uuid: 12345678-1234-1234-1234-123456789abc\n"
        "version: 1\nnext_number: 2\n"
    )
    (data / "sections/content-0001.md").write_text(
        "---\nid: content-0001\n---\n# Test\n"
    )


def test_migrate_project_is_deprecated_alias(tmp_path: Path) -> None:
    """migrate project should be a deprecated alias for migrate plan project-layout."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "project"]
    )
    payload = _json_result(result)
    # Should warn about deprecation
    assert any("deprecated" in str(w).lower() for w in payload.get("warnings", []))
    # Should have replacement command in warning
    assert any("project-layout" in str(w) for w in payload.get("warnings", []))


def test_migrate_project_apply_is_deprecated_alias(tmp_path: Path) -> None:
    """migrate project --apply should be a deprecated alias."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "project", "--apply"]
    )
    payload = _json_result(result)
    # Should warn about deprecation
    assert any("deprecated" in str(w).lower() for w in payload.get("warnings", []))


def test_migrate_ids_is_deprecated_alias(tmp_path: Path) -> None:
    """migrate ids should be a deprecated alias."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "migrate", "ids", "--to", "ledgercore"]
    )
    # Should not crash
    assert result.exit_code != 2  # Not "no such command"
    payload = _json_result(result)
    assert any("deprecated" in str(w).lower() for w in payload.get("warnings", []))


def test_migrate_metadata_is_deprecated_alias(tmp_path: Path) -> None:
    """migrate metadata should be a deprecated alias."""
    _legacy_project(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "migrate", "metadata", "--to", "versioned"],
    )
    # Should not crash
    assert result.exit_code != 2
    payload = _json_result(result)
    assert any("deprecated" in str(w).lower() for w in payload.get("warnings", []))
