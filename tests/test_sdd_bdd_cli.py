"""Tests for SDD BDD-specific checks (SDD-BDD-* rules)."""

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


def _init_sdd(path: Path) -> None:
    """Init project with SDD profile enabled."""
    result = runner.invoke(app, ["--root", str(path), "init", "--profile", "sdd"])
    assert result.exit_code == 0, result.stdout


def _accept_record(record_path: Path) -> None:
    """Set a record's status to accepted."""
    metadata, body = read_front_matter_document(record_path)
    metadata["status"] = "accepted"
    write_front_matter_document(record_path, metadata, body)


def _set_bdd(record_path: Path, bdd: dict) -> None:
    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"] = bdd
    write_front_matter_document(record_path, metadata, body)


def _create_runtime_scenario(tmp_path: Path, title: str = "S") -> Path:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", title],
    )
    assert result.exit_code == 0, result.stdout
    return Path(json.loads(result.stdout)["result"]["path"])


def _run_sdd_check(tmp_path: Path, *, strict: bool = False) -> dict:
    cmd = ["--root", str(tmp_path), "--json", "sdd", "check"]
    if strict:
        cmd.append("--strict")
    result = runner.invoke(app, cmd)
    payload = json.loads(result.stdout)
    if payload.get("ok"):
        data = payload["result"]
    else:
        data = payload["error"]["details"]
    return {"exit_code": result.exit_code, "payload": payload, "data": data}


def test_sdd_bdd_shape_fails_on_structurally_invalid_bdd(tmp_path: Path) -> None:
    """SDD-BDD-SHAPE: structurally invalid bdd is an error."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(record_path, "not-a-mapping")

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    assert any(e["code"] == "SDD-BDD-SHAPE" for e in errors)


def test_sdd_bdd_gwt_fails_when_gwt_missing_for_runtime_scenario(
    tmp_path: Path,
) -> None:
    """SDD-BDD-GWT: missing given/when/then is an error for runtime_scenario."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": [],  # empty
            "when": ["w"],
            "then": ["t"],
        },
    )

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    assert any(e["code"] == "SDD-BDD-GWT" for e in errors)


def test_sdd_bdd_gwt_passes_when_gwt_present(tmp_path: Path) -> None:
    """SDD-BDD-GWT passes when given/when/then are all non-empty."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
        },
    )

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    assert not any(e["code"] == "SDD-BDD-GWT" for e in errors)


def test_sdd_bdd_automation_warns_when_pending(tmp_path: Path) -> None:
    """SDD-BDD-AUTOMATION: warn on pending automation (default policy)."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
        },
    )

    result = _run_sdd_check(tmp_path)
    warnings = result["data"]["warnings"]
    assert any(w["code"] == "SDD-BDD-AUTOMATION" for w in warnings)


def test_sdd_bdd_automation_error_when_required_by_config(tmp_path: Path) -> None:
    """SDD-BDD-AUTOMATION: error when profile requires automation."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
        },
    )

    # Enable require_bdd_automation in config
    # SDD profile init may create archledger.toml or .archledger.toml
    for candidate in (tmp_path / "archledger.toml", tmp_path / ".archledger.toml"):
        if candidate.exists():
            config_path = candidate
            break
    else:
        raise AssertionError("No config file found")
    text = config_path.read_text()
    text = text.replace(
        "require_bdd_automation_for_accepted_records = false",
        "require_bdd_automation_for_accepted_records = true",
    )
    config_path.write_text(text)

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    assert any(e["code"] == "SDD-BDD-AUTOMATION" for e in errors)


def test_sdd_bdd_feature_ref_fails_when_feature_file_not_linked(
    tmp_path: Path,
) -> None:
    """SDD-BDD-FEATURE-REF: feature_file must be in source_refs role=documents."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {
                "status": "linked",
                "feature_file": (
                    "specs/behavior/features/task-management/lifecycle.feature"
                ),
            },
        },
    )

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    assert any(e["code"] == "SDD-BDD-FEATURE-REF" for e in errors)


def test_sdd_bdd_feature_ref_passes_when_feature_file_in_source_refs(
    tmp_path: Path,
) -> None:
    """SDD-BDD-FEATURE-REF: passes when feature_file is linked."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {
                "status": "linked",
                "feature_file": (
                    "specs/behavior/features/task-management/lifecycle.feature"
                ),
            },
        },
    )
    # Create the feature file and add a source_ref
    feat_path = (
        tmp_path
        / "specs"
        / "behavior"
        / "features"
        / "task-management"
        / "lifecycle.feature"
    )
    feat_path.parent.mkdir(parents=True, exist_ok=True)
    feat_path.write_text("Feature: lifecycle\n")

    metadata, body = read_front_matter_document(record_path)
    refs = metadata.get("source_refs", [])
    refs.append(
        {
            "path": "specs/behavior/features/task-management/lifecycle.feature",
            "role": "documents",
        }
    )
    metadata["source_refs"] = refs
    write_front_matter_document(record_path, metadata, body)

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    assert not any(e["code"] == "SDD-BDD-FEATURE-REF" for e in errors)


def test_sdd_bdd_feature_ref_fails_when_feature_file_only_in_test_refs(
    tmp_path: Path,
) -> None:
    """Feature files do not satisfy SDD-BDD-FEATURE-REF via test_refs."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {
                "status": "linked",
                "feature_file": (
                    "specs/behavior/features/task-management/lifecycle.feature"
                ),
            },
        },
    )
    metadata, body = read_front_matter_document(record_path)
    metadata["test_refs"] = [
        {
            "path": "specs/behavior/features/task-management/lifecycle.feature",
            "nodeid": "",
            "role": "validates",
        }
    ]
    write_front_matter_document(record_path, metadata, body)

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    assert any(e["code"] == "SDD-BDD-FEATURE-REF" for e in errors)


def test_sdd_bdd_ac_link_warns_for_nonexistent_ac(tmp_path: Path) -> None:
    """SDD-BDD-AC-LINK: warn when referenced AC ID does not exist."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "acceptance_criteria": ["ac-9999"],
        },
    )

    result = _run_sdd_check(tmp_path)
    warnings = result["data"]["warnings"]
    assert any(w["code"] == "SDD-BDD-AC-LINK" for w in warnings)


def test_sdd_bdd_checks_run_only_for_accepted_records(tmp_path: Path) -> None:
    """BDD SDD checks skip draft/proposed records."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path, title="Draft BDD")
    # Do not accept — leave as draft
    _set_bdd(record_path, "not-a-mapping")

    result = _run_sdd_check(tmp_path, strict=True)
    all_codes = {
        f["code"] for f in result["data"]["errors"] + result["data"]["warnings"]
    }
    assert "SDD-BDD-SHAPE" not in all_codes


def test_sdd_bdd_feature_ref_passes_for_imported_records(tmp_path: Path) -> None:
    """P0: importing a feature then accepting must satisfy SDD-BDD-FEATURE-REF.

    The importer sets automation.feature_file and a documents source_ref, so the
    accepted record must not raise SDD-BDD-FEATURE-REF.
    """
    _init_sdd(tmp_path)
    feature_rel = "specs/behavior/features/task-management/lifecycle.feature"
    feat_path = tmp_path / feature_rel
    feat_path.parent.mkdir(parents=True, exist_ok=True)
    feat_path.write_text(
        "Feature: Task lifecycle\n"
        "  Scenario: Blocked\n"
        "    Given g\n    When w\n    Then t\n",
        encoding="utf-8",
    )
    imported = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "import",
            feature_rel,
            "--kind",
            "runtime-scenario",
            "--status",
            "accepted",
        ],
    )
    assert imported.exit_code == 0, imported.stdout
    result = _run_sdd_check(tmp_path)
    codes = {f["code"] for f in result["data"]["errors"] + result["data"]["warnings"]}
    assert "SDD-BDD-FEATURE-REF" not in codes


def _enable_required_automation(tmp_path: Path) -> None:
    """Flip require_bdd_automation_for_accepted_records to true in config."""
    for candidate in (tmp_path / "archledger.toml", tmp_path / ".archledger.toml"):
        if candidate.exists():
            config_path = candidate
            break
    else:
        raise AssertionError("No config file found")
    text = config_path.read_text()
    text = text.replace(
        "require_bdd_automation_for_accepted_records = false",
        "require_bdd_automation_for_accepted_records = true",
    )
    config_path.write_text(text)


def test_sdd_bdd_automation_linked_fails_when_required(tmp_path: Path) -> None:
    """ac-0006: under strict policy, status=linked is an error (Option A)."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {
                "status": "linked",
                "feature_file": (
                    "specs/behavior/features/task-management/lifecycle.feature"
                ),
            },
            "source_refs": [
                {
                    "path": "specs/behavior/features/task-management/lifecycle.feature",
                    "role": "documents",
                },
            ],
        },
    )
    _enable_required_automation(tmp_path)

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    automation = [e for e in errors if e["code"] == "SDD-BDD-AUTOMATION"]
    assert automation, "expected an SDD-BDD-AUTOMATION error for status=linked"
    assert "linked" in automation[0]["message"]


def test_sdd_bdd_automation_automated_passes_when_required(tmp_path: Path) -> None:
    """ac-0006: status=automated satisfies the strict policy; not_applicable too."""
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {
                "status": "automated",
                "feature_file": (
                    "specs/behavior/features/task-management/lifecycle.feature"
                ),
                "command": "pytest -q",
            },
        },
    )
    metadata, body = read_front_matter_document(record_path)
    metadata["source_refs"] = [
        {
            "path": "specs/behavior/features/task-management/lifecycle.feature",
            "role": "documents",
        }
    ]
    metadata["test_refs"] = [
        "tests/test_task_management_lifecycle.py::test_lifecycle_gate"
    ]
    write_front_matter_document(record_path, metadata, body)
    _enable_required_automation(tmp_path)

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    assert not any(e["code"] == "SDD-BDD-AUTOMATION" for e in errors)
    assert not any(e["code"] == "SDD-BDD-TEST-REF" for e in errors)


def test_sdd_bdd_test_ref_warns_when_automated_without_test_refs(
    tmp_path: Path,
) -> None:
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {
                "status": "automated",
                "feature_file": (
                    "specs/behavior/features/task-management/lifecycle.feature"
                ),
                "command": "pytest -q",
            },
        },
    )
    metadata, body = read_front_matter_document(record_path)
    metadata["source_refs"] = [
        {
            "path": "specs/behavior/features/task-management/lifecycle.feature",
            "role": "documents",
        }
    ]
    write_front_matter_document(record_path, metadata, body)

    result = _run_sdd_check(tmp_path)
    warnings = result["data"]["warnings"]
    assert any(w["code"] == "SDD-BDD-TEST-REF" for w in warnings)


def test_sdd_bdd_test_ref_errors_when_required_and_missing(tmp_path: Path) -> None:
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {
                "status": "automated",
                "feature_file": (
                    "specs/behavior/features/task-management/lifecycle.feature"
                ),
                "command": "pytest -q",
            },
        },
    )
    metadata, body = read_front_matter_document(record_path)
    metadata["source_refs"] = [
        {
            "path": "specs/behavior/features/task-management/lifecycle.feature",
            "role": "documents",
        }
    ]
    write_front_matter_document(record_path, metadata, body)
    _enable_required_automation(tmp_path)

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    assert any(e["code"] == "SDD-BDD-TEST-REF" for e in errors)


def test_sdd_bdd_feature_path_convention_warns_for_deprecated_path(
    tmp_path: Path,
) -> None:
    _init_sdd(tmp_path)
    record_path = _create_runtime_scenario(tmp_path)
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {
                "status": "linked",
                "feature_file": "tests/bdd/features/lifecycle.feature",
            },
        },
    )
    metadata, body = read_front_matter_document(record_path)
    metadata["source_refs"] = [
        {"path": "tests/bdd/features/lifecycle.feature", "role": "documents"}
    ]
    write_front_matter_document(record_path, metadata, body)

    result = _run_sdd_check(tmp_path)
    warnings = result["data"]["warnings"]
    assert any(w["code"] == "SDD-BDD-FEATURE-PATH-CONVENTION" for w in warnings)


def test_sdd_bdd_gwt_fails_for_quality_scenario_when_policy_enabled(
    tmp_path: Path,
) -> None:
    """ac-0007: SDD-BDD-GWT applies to quality_scenario too, not just runtime."""
    _init_sdd(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "quality_scenario",
            "Q",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    _accept_record(record_path)
    _set_bdd(
        record_path,
        {
            "feature": "F",
            "scenario": "Q",
            "given": [],
            "when": ["w"],
            "then": ["t"],
        },
    )

    result = _run_sdd_check(tmp_path)
    errors = result["data"]["errors"]
    gwt = [e for e in errors if e["code"] == "SDD-BDD-GWT"]
    assert gwt, "expected an SDD-BDD-GWT error for quality_scenario"
    assert "quality_scenario" in gwt[0]["message"]
