"""Tests for archledger bdd export CLI command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)

runner = CliRunner()


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout


def _create_record_with_bdd(tmp_path: Path) -> str:
    """Create a runtime_scenario with bdd metadata and return its id."""
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "My scenario"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    record_id = payload["result"]["id"]
    record_path = Path(payload["result"]["path"])

    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"] = {
        "feature": "F",
        "rule": "R",
        "scenario": "My scenario",
        "tags": ["t1"],
        "given": ["g1"],
        "when": ["w1"],
        "then": ["t1"],
        "automation": {"status": "linked"},
    }
    write_front_matter_document(record_path, metadata, body)
    return record_id


def test_bdd_export_creates_feature_file(tmp_path: Path) -> None:
    """ac-0011: export creates a .feature file from a record with bdd metadata."""
    _init(tmp_path)
    record_id = _create_record_with_bdd(tmp_path)
    out_rel = "out.feature"
    out = tmp_path / out_rel

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            out_rel,
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["record_id"] == record_id
    assert payload["schema"] == "archledger.bdd-export.v1"

    content = out.read_text(encoding="utf-8")
    assert f"Generated from archledger record {record_id}" in content
    assert "Feature: F" in content
    assert "Rule: R" in content
    assert "Scenario: My scenario" in content
    assert "Given g1" in content
    assert "When w1" in content
    assert "Then t1" in content


def test_bdd_export_refuses_records_without_bdd(tmp_path: Path) -> None:
    """ac-0011: export refuses records without bdd metadata."""
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "No BDD"],
    )
    assert result.exit_code == 0, result.stdout
    record_id = json.loads(result.stdout)["result"]["id"]

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            str(tmp_path / "out.feature"),
        ],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert "no bdd" in payload["error"]["message"].lower()


def test_bdd_export_is_deterministic(tmp_path: Path) -> None:
    """ac-0011: export produces identical content on repeated runs."""
    _init(tmp_path)
    record_id = _create_record_with_bdd(tmp_path)
    out1_rel = "out1.feature"
    out2_rel = "out2.feature"
    out1 = tmp_path / out1_rel
    out2 = tmp_path / out2_rel

    for out_rel in [out1_rel, out2_rel]:
        result = runner.invoke(
            app,
            [
                "--root",
                str(tmp_path),
                "--json",
                "bdd",
                "export",
                record_id,
                "--out",
                out_rel,
            ],
        )
        assert result.exit_code == 0, result.stdout

    assert out1.read_text() == out2.read_text()


def test_bdd_export_json_schema_matches() -> None:
    """ac-0010: the bdd-export JSON schema target exists and is loadable."""
    from archledger.jsonschemas import SCHEMA_FILES, load_json_schema

    assert "bdd-export" in SCHEMA_FILES
    schema = load_json_schema("bdd-export")
    assert schema["title"] == "Archledger BDD export result"
    assert "record_id" in schema["required"]


# ---- P0: export path validation + overwrite protection ----


def test_bdd_export_refuses_absolute_outside_workspace_by_default(
    tmp_path: Path,
) -> None:
    """P0: --out must be a safe relative POSIX path inside the workspace."""
    _init(tmp_path)
    record_id = _create_record_with_bdd(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            "/tmp/should-be-refused.feature",
        ],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    msg = payload["error"]["message"].lower()
    assert "absolute" in msg or "relative" in msg or "workspace" in msg


def test_bdd_export_does_not_write_before_path_validation(tmp_path: Path) -> None:
    """P0: no file is written when path validation fails."""
    _init(tmp_path)
    record_id = _create_record_with_bdd(tmp_path)
    # A parent-escape path is refused by validate_relative_posix_path.
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            "../al_export_refused_unique.feature",
        ],
    )
    assert result.exit_code != 0
    # Nothing should have been written outside the workspace.
    assert not (tmp_path.parent / "al_export_refused_unique.feature").exists()


def test_bdd_export_refuses_overwrite_without_force(tmp_path: Path) -> None:
    """P0: overwriting an existing file requires --force."""
    _init(tmp_path)
    record_id = _create_record_with_bdd(tmp_path)
    existing = tmp_path / "out.feature"
    existing.write_text("PRE-EXISTING\n", encoding="utf-8")
    # First attempt without --force must fail and must not overwrite.
    refused = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            "out.feature",
        ],
    )
    assert refused.exit_code != 0
    assert existing.read_text(encoding="utf-8") == "PRE-EXISTING\n"
    # With --force it succeeds and overwrites.
    forced = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            "out.feature",
            "--force",
        ],
    )
    assert forced.exit_code == 0, forced.stdout
    assert "PRE-EXISTING" not in existing.read_text(encoding="utf-8")
