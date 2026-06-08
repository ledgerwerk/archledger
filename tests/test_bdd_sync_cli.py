"""Tests for archledger bdd sync CLI command."""

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
    result = runner.invoke(app, ["--root", str(path), "init", "--profile", "sdd"])
    assert result.exit_code == 0, result.stdout


def _create_bdd_record(
    tmp_path: Path,
    *,
    bdd: dict,
    title: str = "Scenario",
    status: str = "accepted",
) -> str:
    """Create a runtime_scenario, write bdd metadata, return its id and path."""
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "runtime_scenario",
            title,
        ],
    )
    assert created.exit_code == 0, created.stdout
    payload = json.loads(created.stdout)
    record_id = payload["result"]["id"]
    record_path = Path(payload["result"]["path"])

    metadata, body = read_front_matter_document(record_path)
    metadata["status"] = status
    metadata["bdd"] = bdd
    write_front_matter_document(record_path, metadata, body)
    return record_id


def _sync(tmp_path: Path):
    return runner.invoke(
        app, ["--root", str(tmp_path), "--json", "bdd", "sync", "--check"]
    )


def _no_drift_bdd(feature_file: str, scenario: str = "Scenario") -> dict:
    return {
        "feature": "Lifecycle",
        "rule": "Accepted plan required",
        "scenario": scenario,
        "given": ["a task has no accepted plan"],
        "when": ["an agent starts implementation"],
        "then": ["SDD validation reports a missing accepted plan"],
        "automation": {"status": "linked", "feature_file": feature_file},
        "source_refs": [
            {"path": feature_file, "role": "documents"},
        ],
    }


def test_bdd_sync_no_drift_after_import(tmp_path: Path) -> None:
    """A clean imported feature has no sync findings."""
    _init(tmp_path)
    feature = (
        tmp_path
        / "specs"
        / "behavior"
        / "features"
        / "task-management"
        / "lifecycle.feature"
    )
    feature.parent.mkdir(parents=True, exist_ok=True)
    feature.write_text(
        "Feature: Lifecycle\n"
        "  Rule: Accepted plan required\n"
        "    Scenario: Scenario\n"
        "      Given a task has no accepted plan\n"
        "      When an agent starts implementation\n"
        "      Then SDD validation reports a missing accepted plan\n",
        encoding="utf-8",
    )
    rel = str(feature.relative_to(tmp_path))
    imported = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "import",
            rel,
            "--kind",
            "runtime-scenario",
            "--status",
            "accepted",
        ],
    )
    assert imported.exit_code == 0, imported.stdout

    result = _sync(tmp_path)
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["findings"] == []
    assert payload["checked"] >= 1
    assert payload["feature_files_checked"] >= 1


def test_bdd_sync_missing_feature_file(tmp_path: Path) -> None:
    """A linked feature file that does not exist is BDD-SYNC-FILE-MISSING."""
    _init(tmp_path)
    _create_bdd_record(
        tmp_path,
        bdd=_no_drift_bdd("specs/behavior/features/task-management/missing.feature"),
    )

    result = _sync(tmp_path)
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    codes = [f["code"] for f in payload["findings"]]
    assert "BDD-SYNC-FILE-MISSING" in codes


def test_bdd_sync_scenario_missing_from_feature(tmp_path: Path) -> None:
    """A record's scenario absent from the feature file is reported."""
    _init(tmp_path)
    feature = (
        tmp_path
        / "specs"
        / "behavior"
        / "features"
        / "task-management"
        / "lifecycle.feature"
    )
    feature.parent.mkdir(parents=True, exist_ok=True)
    # The feature has a different scenario name than the record expects.
    feature.write_text(
        "Feature: Lifecycle\n"
        "  Rule: Accepted plan required\n"
        "    Scenario: Something Else\n"
        "      Given a task has no accepted plan\n"
        "      When an agent starts implementation\n"
        "      Then SDD validation reports a missing accepted plan\n",
        encoding="utf-8",
    )
    _create_bdd_record(
        tmp_path,
        bdd=_no_drift_bdd("specs/behavior/features/task-management/lifecycle.feature"),
    )

    result = _sync(tmp_path)
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    codes = [f["code"] for f in payload["findings"]]
    assert "BDD-SYNC-SCENARIO-MISSING" in codes


def test_bdd_sync_gwt_mismatch(tmp_path: Path) -> None:
    """A modified Given/When/Then step is BDD-SYNC-GWT-MISMATCH."""
    _init(tmp_path)
    feature = (
        tmp_path
        / "specs"
        / "behavior"
        / "features"
        / "task-management"
        / "lifecycle.feature"
    )
    feature.parent.mkdir(parents=True, exist_ok=True)
    feature.write_text(
        "Feature: Lifecycle\n"
        "  Rule: Accepted plan required\n"
        "    Scenario: Scenario\n"
        "      Given a DIFFERENT given step\n"
        "      When an agent starts implementation\n"
        "      Then SDD validation reports a missing accepted plan\n",
        encoding="utf-8",
    )
    _create_bdd_record(
        tmp_path,
        bdd=_no_drift_bdd("specs/behavior/features/task-management/lifecycle.feature"),
    )

    result = _sync(tmp_path)
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    codes = [f["code"] for f in payload["findings"]]
    assert "BDD-SYNC-GWT-MISMATCH" in codes


def test_bdd_sync_orphan_scenario_in_feature(tmp_path: Path) -> None:
    """An extra scenario in the feature file with no matching record is orphan."""
    _init(tmp_path)
    feature = (
        tmp_path
        / "specs"
        / "behavior"
        / "features"
        / "task-management"
        / "lifecycle.feature"
    )
    feature.parent.mkdir(parents=True, exist_ok=True)
    feature.write_text(
        "Feature: Lifecycle\n"
        "  Rule: Accepted plan required\n"
        "    Scenario: Scenario\n"
        "      Given a task has no accepted plan\n"
        "      When an agent starts implementation\n"
        "      Then SDD validation reports a missing accepted plan\n"
        "    Scenario: Orphan Scenario\n"
        "      Given x\n      When y\n      Then z\n",
        encoding="utf-8",
    )
    _create_bdd_record(
        tmp_path,
        bdd=_no_drift_bdd("specs/behavior/features/task-management/lifecycle.feature"),
    )

    result = _sync(tmp_path)
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    codes = [f["code"] for f in payload["findings"]]
    assert "BDD-SYNC-ORPHAN-SCENARIO" in codes


def test_bdd_sync_requires_check_returns_json_error(tmp_path: Path) -> None:
    """P0: bdd sync without --check returns a JSON error envelope."""
    _init(tmp_path)
    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "bdd", "sync"])
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "bdd sync"
    assert "Pass --check" in payload["error"]["message"]


def test_bdd_sync_invalid_feature_file_returns_structured_error(
    tmp_path: Path,
) -> None:
    """An unparseable feature file yields a structured JSON error envelope."""
    _init(tmp_path)
    feature = (
        tmp_path / "specs" / "behavior" / "features" / "task-management" / "bad.feature"
    )
    feature.parent.mkdir(parents=True, exist_ok=True)
    feature.write_text("Background:\n  this is unsupported\n", encoding="utf-8")
    _create_bdd_record(
        tmp_path,
        bdd=_no_drift_bdd("specs/behavior/features/task-management/bad.feature"),
    )

    result = _sync(tmp_path)
    # Sync reports findings for the linked file; it should not crash with a
    # traceback. The command must return JSON.
    payload = json.loads(result.stdout)
    assert payload["command"] == "bdd sync"
    assert "findings" in payload.get("result", payload)


def test_bdd_sync_warns_for_deprecated_feature_path(tmp_path: Path) -> None:
    _init(tmp_path)
    _create_bdd_record(tmp_path, bdd=_no_drift_bdd("tests/bdd/features/legacy.feature"))

    result = _sync(tmp_path)
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    codes = [f["code"] for f in payload["findings"]]
    assert "BDD-FEATURE-PATH-CONVENTION" in codes
