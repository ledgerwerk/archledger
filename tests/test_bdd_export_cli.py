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
    out = tmp_path / "out.feature"

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
            str(out),
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
    out1 = tmp_path / "out1.feature"
    out2 = tmp_path / "out2.feature"

    for out in [out1, out2]:
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
                str(out),
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
