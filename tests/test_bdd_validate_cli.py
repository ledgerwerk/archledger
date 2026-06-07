"""Tests for archledger bdd validate CLI command."""

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


def _create_record_with_bdd(
    tmp_path: Path, bdd: dict, *, title: str = "S", status: str = "accepted"
) -> str:
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "runtime_scenario",
            title,
            "--status",
            status,
        ],
    )
    assert created.exit_code == 0, created.stdout
    payload = json.loads(created.stdout)["result"]
    record_path = Path(payload["path"])
    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"] = bdd
    write_front_matter_document(record_path, metadata, body)
    return payload["id"]


def test_bdd_validate_record_valid(tmp_path: Path) -> None:
    _init(tmp_path)
    rid = _create_record_with_bdd(
        tmp_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "linked", "feature_file": "x.feature"},
        },
    )
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "validate", rid],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.bdd-validate.v1"
    assert payload["valid"] is True
    assert payload["findings"] == []


def test_bdd_validate_record_incomplete_gwt(tmp_path: Path) -> None:
    _init(tmp_path)
    rid = _create_record_with_bdd(
        tmp_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": [],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "pending"},
        },
    )
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "validate", rid],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["valid"] is False
    codes = {f["code"] for f in payload["findings"]}
    assert "BDD-GWT-INCOMPLETE" in codes


def test_bdd_validate_feature_file_reports_line_numbers(tmp_path: Path) -> None:
    _init(tmp_path)
    feat = tmp_path / "bad.feature"
    feat.write_text("Feature: F\n  Background:\n    Given g\n", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "validate",
            "--feature-file",
            "bad.feature",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["valid"] is False
    finding = payload["findings"][0]
    assert finding["line"] == 2
    assert finding["code"] == "BDD-GHERKIN-UNSUPPORTED"


def test_bdd_validate_feature_file_ok(tmp_path: Path) -> None:
    _init(tmp_path)
    feat = tmp_path / "ok.feature"
    feat.write_text(
        "Feature: F\n  Scenario: A\n    Given g\n    When w\n    Then t\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "validate",
            "--feature-file",
            "ok.feature",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["valid"] is True
    assert len(payload["scenarios"]) == 1


def test_bdd_validate_all(tmp_path: Path) -> None:
    _init(tmp_path)
    _create_record_with_bdd(
        tmp_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "pending"},
        },
        title="Good",
    )
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "validate", "--all"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["target"] == "all"
    assert payload["valid"] is True


def test_bdd_validate_requires_target(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "validate"],
    )
    assert result.exit_code != 0


# ---- bdd list and bdd status ----


def _mk_bdd_record(tmp_path, runner_app, title, bdd, status="accepted"):
    created = runner_app.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "runtime_scenario",
            title,
            "--status",
            status,
        ],
    )
    payload = json.loads(created.stdout)["result"]
    record_path = Path(payload["path"])
    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"] = bdd
    write_front_matter_document(record_path, metadata, body)
    return payload["id"]


def test_bdd_list_lists_all_bdd_records(tmp_path: Path) -> None:
    _init(tmp_path)
    _mk_bdd_record(
        tmp_path,
        runner,
        "A",
        {
            "feature": "F",
            "scenario": "A",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "linked", "feature_file": "f.feature"},
        },
    )
    _mk_bdd_record(
        tmp_path,
        runner,
        "B",
        {
            "feature": "F",
            "scenario": "B",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "pending"},
        },
    )
    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "bdd", "list"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.bdd-list.v1"
    assert payload["count"] == 2


def test_bdd_list_filters_by_automation(tmp_path: Path) -> None:
    _init(tmp_path)
    _mk_bdd_record(
        tmp_path,
        runner,
        "A",
        {
            "feature": "F",
            "scenario": "A",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "linked"},
        },
    )
    _mk_bdd_record(
        tmp_path,
        runner,
        "B",
        {
            "feature": "F",
            "scenario": "B",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "pending"},
        },
    )
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "list", "--automation", "pending"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["count"] == 1
    assert payload["entries"][0]["automation_status"] == "pending"


def test_bdd_status_summarizes_coverage(tmp_path: Path) -> None:
    _init(tmp_path)
    _mk_bdd_record(
        tmp_path,
        runner,
        "A",
        {
            "feature": "F",
            "scenario": "A",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "linked", "feature_file": "f.feature"},
        },
    )
    _mk_bdd_record(
        tmp_path,
        runner,
        "B",
        {
            "feature": "F",
            "scenario": "B",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "pending"},
        },
    )
    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "bdd", "status"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.bdd-status.v1"
    assert payload["totals"]["examples"] == 2
    assert payload["coverage"]["complete_gwt"] == {"covered": 2, "total": 2}
    assert payload["coverage"]["linked_feature_files"] == {"covered": 1, "total": 2}
    assert payload["coverage"]["pending"] == {"covered": 1, "total": 2}


# ---- bdd set and bdd link ----


def test_bdd_set_creates_bdd_block(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "S"],
    )
    rid = json.loads(created.stdout)["result"]["id"]
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "set",
            rid,
            "--feature",
            "F",
            "--scenario",
            "A",
            "--given",
            "g",
            "--when",
            "w",
            "--then",
            "t",
            "--tag",
            "tag1",
            "--tag",
            "tag2",
            "--automation-status",
            "linked",
            "--feature-file",
            "f.feature",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]["bdd"]
    assert payload["feature"] == "F"
    assert payload["given"] == ["g"]
    assert payload["tags"] == ["tag1", "tag2"]
    assert payload["automation"]["status"] == "linked"
    assert payload["automation"]["feature_file"] == "f.feature"


def test_bdd_set_patches_existing_bdd(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "S"],
    )
    rid = json.loads(created.stdout)["result"]["id"]
    # First set
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "set",
            rid,
            "--feature",
            "F1",
            "--scenario",
            "S1",
        ],
    )
    # Patch feature only
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "set", rid, "--feature", "F2"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]["bdd"]
    assert payload["feature"] == "F2"
    assert payload["scenario"] == "S1"  # preserved


def test_bdd_link_sets_automation_and_source_ref(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "S"],
    )
    rid = json.loads(created.stdout)["result"]["id"]
    rp = Path(json.loads(created.stdout)["result"]["path"])
    # Set minimal bdd first
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "set",
            rid,
            "--feature",
            "F",
            "--scenario",
            "A",
            "--given",
            "g",
            "--when",
            "w",
            "--then",
            "t",
        ],
    )
    # Link
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "link",
            rid,
            "--feature-file",
            "tests/bdd/f.feature",
            "--scenario",
            "A",
            "--command",
            "pytest -q tests/bdd",
            "--status",
            "automated",
        ],
    )
    assert result.exit_code == 0, result.stdout
    auto = json.loads(result.stdout)["result"]["automation"]
    assert auto["feature_file"] == "tests/bdd/f.feature"
    assert auto["command"] == "pytest -q tests/bdd"
    assert auto["status"] == "automated"
    metadata, _body = read_front_matter_document(rp)
    assert any(ref["role"] == "documents" for ref in metadata.get("source_refs", []))


def test_bdd_link_refuses_without_bdd_metadata(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "S"],
    )
    rid = json.loads(created.stdout)["result"]["id"]
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "link",
            rid,
            "--feature-file",
            "f.feature",
        ],
    )
    assert result.exit_code != 0
