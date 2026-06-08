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


def _init_arc42(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init", "--profile", "arc42"])
    assert result.exit_code == 0, result.stdout


def _write_sdd_policy(path: Path, **flags: bool) -> None:
    text = path.read_text(encoding="utf-8")
    for key, value in flags.items():
        candidates = (
            f"{key} = true",
            f"{key} = false",
        )
        replacement = f"{key} = {str(value).lower()}"
        for candidate in candidates:
            if candidate in text:
                text = text.replace(candidate, replacement)
                break
        else:
            raise AssertionError(f"{key} not found in {path}")
    path.write_text(text, encoding="utf-8")


def _accepted_requirement_with(
    tmp_path: Path,
    body: str,
    metadata_overrides: dict,
) -> Path:
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Requirement",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(record_path)
    metadata.update(metadata_overrides)
    write_front_matter_document(record_path, metadata, body)
    return record_path


BODY = "Implemented requirement with a real body.\n"


def test_sdd_check_reports_missing_source_and_test_refs(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Traceable requirement",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    result = json.loads(created.stdout)["result"]
    record_path = Path(result["path"])
    metadata, _body = read_front_matter_document(record_path)
    metadata["source_refs"] = [{"path": "src/missing.py", "role": "implements"}]
    metadata["test_refs"] = ["tests/test_missing.py::test_it"]
    metadata["acceptance_criteria"] = [{"statement": "It works."}]
    write_front_matter_document(record_path, metadata, "Implemented requirement.\n")
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 1
    payload = json.loads(checked.stdout)
    codes = {item["code"] for item in payload["error"]["details"]["errors"]}
    assert "SDD-SOURCE-REF-EXISTS" in codes
    assert "SDD-TEST-REF-EXISTS" in codes


def test_sdd_check_uses_config_policy_flags(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    _write_sdd_policy(
        tmp_path / "archledger.toml",
        require_acceptance_criteria=False,
        require_implementation_refs=False,
        require_test_refs=False,
    )
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Config disabled policy",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(record_path)
    write_front_matter_document(record_path, metadata, BODY)
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 0, checked.stdout
    payload = json.loads(checked.stdout)["result"]
    assert payload["policy"] == {
        "require_acceptance_criteria": False,
        "require_implementation_refs": False,
        "require_test_refs": False,
        "require_bdd_gwt_for_behavior_records": True,
        "require_bdd_automation_for_accepted_records": False,
    }
    assert payload["schema"] == "archledger.sdd-check.v2"
    assert "profile" not in payload
    assert "profile_enabled" not in payload
    assert payload["sdd_enabled"] is True
    assert payload["default_profile"] == "sdd"
    assert "sdd" in payload["enabled_profiles"]


def test_sdd_check_cli_overrides_config_policy_flags(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    _write_sdd_policy(
        tmp_path / "archledger.toml",
        require_test_refs=False,
    )
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Impl without validation",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(record_path)
    metadata["source_refs"] = [{"path": "src/feature.py", "role": "implements"}]
    metadata["acceptance_criteria"] = [{"statement": "It works."}]
    write_front_matter_document(record_path, metadata, BODY)
    checked = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "check",
            "--require-test-refs",
        ],
    )
    assert checked.exit_code == 1, checked.stdout
    payload = json.loads(checked.stdout)["error"]["details"]
    codes = {item["code"] for item in payload["errors"]}
    assert "SDD-REQ-TEST" in codes
    assert payload["policy"]["require_test_refs"] is True
    p = payload["policy"]
    assert p["require_implementation_refs"] is True


def test_sdd_check_can_disable_acceptance_criteria(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_value():\n    assert True\n",
        encoding="utf-8",
    )
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "No AC",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(record_path)
    metadata["source_refs"] = [{"path": "src/feature.py", "role": "implements"}]
    metadata["test_refs"] = ["tests/test_feature.py::test_value"]
    metadata.pop("acceptance_criteria", None)
    write_front_matter_document(record_path, metadata, BODY)
    default = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert default.exit_code == 1, default.stdout
    default_codes = {
        item["code"]
        for item in json.loads(default.stdout)["error"]["details"]["errors"]
    }
    assert "SDD-REQ-AC" in default_codes
    checked = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "check",
            "--no-require-acceptance-criteria",
        ],
    )
    assert checked.exit_code == 0, checked.stdout


def test_sdd_check_reports_malformed_ac_without_traceback(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_value():\n    assert True\n",
        encoding="utf-8",
    )
    _accepted_requirement_with(
        tmp_path,
        BODY,
        {
            "source_refs": [{"path": "src/feature.py", "role": "implements"}],
            "test_refs": ["tests/test_feature.py::test_value"],
            "acceptance_criteria": [{"statement": "ok", "validation": "manual"}],
        },
    )
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 1, checked.stdout
    payload = json.loads(checked.stdout)["error"]["details"]
    codes = {item["code"] for item in payload["errors"]}
    assert "SDD-AC-VALIDATION-FORMAT" in codes


def test_sdd_check_reports_missing_ac_statement(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_value():\n    assert True\n",
        encoding="utf-8",
    )
    _accepted_requirement_with(
        tmp_path,
        BODY,
        {
            "source_refs": [{"path": "src/feature.py", "role": "implements"}],
            "test_refs": ["tests/test_feature.py::test_value"],
            "acceptance_criteria": [
                {},
                {"summary": "no statement key"},
            ],
        },
    )
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 1, checked.stdout
    payload = json.loads(checked.stdout)["error"]["details"]
    codes = {item["code"] for item in payload["errors"]}
    assert "SDD-AC-NO-STATEMENT" in codes


def test_sdd_check_accepts_source_ref_string_with_symbol(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_value():\n    assert True\n",
        encoding="utf-8",
    )
    _accepted_requirement_with(
        tmp_path,
        BODY,
        {
            "source_refs": ["src/feature.py#Feature"],
            "test_refs": ["tests/test_feature.py::test_value"],
            "acceptance_criteria": [{"statement": "It works."}],
        },
    )
    checked = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "check",
            "--no-require-implementation-refs",
        ],
    )
    assert checked.exit_code == 0, checked.stdout
    payload = json.loads(checked.stdout)["result"]
    codes = {item["code"] for item in payload["errors"]}
    assert "SDD-SOURCE-REF-EXISTS" not in codes


def test_sdd_check_reports_malformed_source_ref_path(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_value():\n    assert True\n",
        encoding="utf-8",
    )
    _accepted_requirement_with(
        tmp_path,
        BODY,
        {
            "source_refs": [
                {
                    "path": "../outside.py",
                    "role": "implements",
                },
                {
                    "path": "src/feature.py",
                    "role": "implements",
                },
            ],
            "test_refs": ["tests/test_feature.py::test_value"],
            "acceptance_criteria": [{"statement": "It works."}],
        },
    )
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 1, checked.stdout
    payload = json.loads(checked.stdout)["error"]["details"]
    codes = {item["code"] for item in payload["errors"]}
    assert "SDD-SOURCE-REF-PATH" in codes


def test_sdd_check_reports_malformed_test_ref_path(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    _accepted_requirement_with(
        tmp_path,
        BODY,
        {
            "source_refs": [{"path": "src/feature.py", "role": "implements"}],
            "test_refs": ["/absolute/test.py::test_x"],
            "acceptance_criteria": [{"statement": "It works."}],
        },
    )
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 1, checked.stdout
    payload = json.loads(checked.stdout)["error"]["details"]
    codes = {item["code"] for item in payload["errors"]}
    assert "SDD-TEST-REF-PATH" in codes


def test_sdd_check_records_checked_excludes_draft(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_value():\n    assert True\n",
        encoding="utf-8",
    )
    _accepted_requirement_with(
        tmp_path,
        BODY,
        {
            "source_refs": [{"path": "src/feature.py", "role": "implements"}],
            "test_refs": ["tests/test_feature.py::test_value"],
            "acceptance_criteria": [{"statement": "It works."}],
        },
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Draft requirement",
            "--status",
            "draft",
        ],
    )
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 0, checked.stdout
    summary = json.loads(checked.stdout)["result"]["summary"]
    assert summary["records_total"] == 2
    assert summary["records_checked"] == 1
    checked2 = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "check",
            "--include-drafts",
        ],
    )
    assert checked2.exit_code == 0, checked2.stdout
    summary2 = json.loads(checked2.stdout)["result"]["summary"]
    assert summary2["records_total"] == 2
    assert summary2["records_checked"] == 2


def test_sdd_check_fails_when_profile_not_enabled(
    tmp_path: Path,
) -> None:
    _init_arc42(tmp_path)
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 1, checked.stdout
    details = json.loads(checked.stdout)["error"]["details"]
    assert details["profile_enabled"] is False


def test_sdd_check_allow_without_profile_requires_reason(
    tmp_path: Path,
) -> None:
    _init_arc42(tmp_path)
    checked = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "check",
            "--allow-without-profile",
        ],
    )
    assert checked.exit_code == 1, checked.stdout
    msg = json.loads(checked.stdout)["error"]["message"]
    assert "--reason" in msg


def test_sdd_check_allow_without_profile_with_reason(
    tmp_path: Path,
) -> None:
    _init_arc42(tmp_path)
    checked = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "check",
            "--allow-without-profile",
            "--reason",
            "ad-hoc lint",
        ],
    )
    assert checked.exit_code == 0, checked.stdout


def test_sdd_check_warns_on_link_to_draft_target(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_value():\n    assert True\n",
        encoding="utf-8",
    )
    draft = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Draft target",
            "--status",
            "draft",
        ],
    )
    assert draft.exit_code == 0, draft.stdout
    draft_id = json.loads(draft.stdout)["result"]["id"]
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Linker",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(record_path)
    metadata["source_refs"] = [{"path": "src/feature.py", "role": "implements"}]
    metadata["test_refs"] = ["tests/test_feature.py::test_value"]
    metadata["acceptance_criteria"] = [{"statement": "It works."}]
    metadata["links"] = [{"rel": "relates_to", "target": draft_id}]
    write_front_matter_document(record_path, metadata, BODY)
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 0, checked.stdout
    payload = json.loads(checked.stdout)["result"]
    warning_codes = {item["code"] for item in payload["warnings"]}
    assert "SDD-LINK-TARGET-STATUS" in warning_codes


# ---- P0: sdd status v2 payload + sdd check BDD overrides ----


def test_sdd_status_reports_sdd_enabled_when_default_profile_is_arc42(
    tmp_path: Path,
) -> None:
    """P0: status must report SDD enabled state, not just the default profile."""
    _init_arc42(tmp_path)
    enable = runner.invoke(app, ["--root", str(tmp_path), "profile", "enable", "sdd"])
    assert enable.exit_code == 0, enable.stdout
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "status"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.sdd-status.v2"
    assert payload["sdd_enabled"] is True
    assert payload["default_profile"] == "arc42"
    assert "sdd" in payload["enabled_profiles"]
    # The legacy single 'profile' field must not be the only signal.
    assert (
        "profile" not in payload
        or payload.get("profile") != "arc42"
        or payload["sdd_enabled"]
    )


def test_sdd_status_json_includes_policy_and_enabled_profiles(tmp_path: Path) -> None:
    """P0: status payload exposes effective policy + enabled profiles."""
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "status"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.sdd-status.v2"
    assert payload["sdd_enabled"] is True
    assert "sdd" in payload["enabled_profiles"]
    assert isinstance(payload["policy"], dict)
    policy = payload["policy"]
    assert policy["require_acceptance_criteria"] is True
    assert policy["require_bdd_gwt_for_behavior_records"] is True
    assert "require_bdd_automation_for_accepted_records" in policy


def test_sdd_status_human_output_says_sdd_enabled(tmp_path: Path) -> None:
    """P0: human status output says 'SDD enabled' and lists profiles."""
    _init_arc42(tmp_path)
    enable = runner.invoke(app, ["--root", str(tmp_path), "profile", "enable", "sdd"])
    assert enable.exit_code == 0, enable.stdout
    result = runner.invoke(app, ["--root", str(tmp_path), "sdd", "status"])
    assert result.exit_code == 0, result.stdout
    text = result.stdout
    assert "SDD enabled: yes" in text
    assert "Default profile: arc42" in text
    assert "sdd" in text


def test_sdd_check_cli_overrides_bdd_gwt_policy(tmp_path: Path) -> None:
    """P0: sdd check can override BDD GWT policy from the CLI."""
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "runtime_scenario",
            "Incomplete GWT",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(record_path)
    metadata["bdd"] = {
        "feature": "F",
        "scenario": "S",
        "given": [],
        "when": ["w"],
        "then": ["t"],
        "automation": {"status": "pending"},
    }
    write_front_matter_document(record_path, metadata, BODY)
    # With --no-require-bdd-gwt the missing given is not an error.
    checked = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "check",
            "--no-require-bdd-gwt",
        ],
    )
    assert checked.exit_code == 0, checked.stdout
    payload = json.loads(checked.stdout)["result"]
    assert payload["policy"]["require_bdd_gwt_for_behavior_records"] is False
    codes = {e["code"] for e in payload["errors"]}
    assert "SDD-BDD-GWT" not in codes


def test_sdd_check_cli_overrides_bdd_automation_policy(tmp_path: Path) -> None:
    """P0: sdd check can override BDD automation policy from the CLI."""
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "runtime_scenario",
            "Pending automation",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(record_path)
    metadata["bdd"] = {
        "feature": "F",
        "scenario": "S",
        "given": ["g"],
        "when": ["w"],
        "then": ["t"],
        "automation": {"status": "pending"},
    }
    write_front_matter_document(record_path, metadata, BODY)
    # With --require-bdd-automation the pending status becomes an error.
    checked = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "check",
            "--require-bdd-automation",
        ],
    )
    assert checked.exit_code == 1, checked.stdout
    details = json.loads(checked.stdout)["error"]["details"]
    assert details["policy"]["require_bdd_automation_for_accepted_records"] is True
    codes = {e["code"] for e in details["errors"]}
    assert "SDD-BDD-AUTOMATION" in codes


# ---- Phase 2: sdd explain (rule registry) ----


def test_sdd_explain_single_rule(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "explain", "SDD-REQ-AC"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.sdd-explain.v1"
    assert payload["code"] == "SDD-REQ-AC"
    assert payload["meaning"]
    assert payload["fix"]
    assert payload["waivable"] is True
    assert "SDD-REQ-AC" in payload["waiver_example"]


def test_sdd_explain_all_lists_every_rule(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "explain", "--all"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    codes = {r["code"] for r in payload["rules"]}
    # Every code actually emitted by the engine must be explained.
    assert "SDD-REQ-AC" in codes
    assert "SDD-BDD-AUTOMATION" in codes
    assert "SDD-PLACEHOLDER" in codes
    assert "SDD-WAIVER-NO-REASON" in codes


def test_sdd_explain_unknown_code(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "explain", "SDD-NOPE"],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert "known_codes" in payload["error"]["details"]


# ---- Phase 2: sdd init ----


def test_sdd_init_enables_sdd_profile_and_writes_block(tmp_path: Path) -> None:
    _init_arc42(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "init"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.sdd-init.v1"
    text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert "[profiles.sdd]" in text
    # sdd status now reports sdd_enabled.
    status = runner.invoke(app, ["--root", str(tmp_path), "--json", "sdd", "status"])
    assert json.loads(status.stdout)["result"]["sdd_enabled"] is True


def test_sdd_init_strict_defaults_and_seed(tmp_path: Path) -> None:
    _init_arc42(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "init",
            "--strict-defaults",
            "--seed",
            "minimal",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["policy"]["require_bdd_automation_for_accepted_records"] is True
    assert len(payload["seeded"]) >= 1
    text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert "require_bdd_automation_for_accepted_records = true" in text


def test_sdd_init_dry_run_does_not_write(tmp_path: Path) -> None:
    _init_arc42(tmp_path)
    before = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "init",
            "--dry-run",
            "--strict-defaults",
            "--seed",
            "minimal",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["dry_run"] is True
    assert payload["seeded"] == []
    # Config untouched.
    assert (tmp_path / "archledger.toml").read_text(encoding="utf-8") == before


# ---- Phase 2: sdd policy show/set ----


def test_sdd_policy_show_reports_effective_policy(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "policy", "show"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.sdd-policy.v1"
    assert payload["sdd_enabled"] is True
    assert payload["policy"]["require_acceptance_criteria"] is True
    assert "require_bdd_automation_for_accepted_records" in payload["policy"]


def test_sdd_policy_set_updates_profiles_sdd_block(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "policy",
            "set",
            "--require-bdd-automation",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert "require_bdd_automation_for_accepted_records" in payload["changed"]
    assert payload["after"]["require_bdd_automation_for_accepted_records"] is True
    text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert "require_bdd_automation_for_accepted_records = true" in text


def test_sdd_policy_set_requires_a_flag(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "policy", "set"],
    )
    assert result.exit_code != 0


# ---- Phase 2: sdd waive add/list/remove ----


def test_sdd_waive_add_requires_reason(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "R",
            "--status",
            "accepted",
        ],
    )
    rid = json.loads(created.stdout)["result"]["id"]
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "waive",
            "add",
            rid,
            "--rule",
            "SDD-REQ-AC",
        ],
    )
    assert result.exit_code != 0


def test_sdd_waive_add_suppresses_matching_rule(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "R",
            "--status",
            "accepted",
        ],
    )
    rid = json.loads(created.stdout)["result"]["id"]
    added = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "waive",
            "add",
            rid,
            "--rule",
            "SDD-REQ-AC",
            "--reason",
            "Legacy external validation.",
        ],
    )
    assert added.exit_code == 0, added.stdout
    # sdd check no longer reports SDD-REQ-AC for this record.
    checked = runner.invoke(app, ["--root", str(tmp_path), "--json", "sdd", "check"])
    payload = json.loads(checked.stdout)
    data = payload.get("result") or payload["error"]["details"]
    codes = {e["code"] for e in data["errors"]}
    assert "SDD-REQ-AC" not in codes
    # The waiver is recorded in front matter.
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(record_path)
    waivers = metadata["sdd"]["waivers"]
    assert any(w["rule"] == "SDD-REQ-AC" for w in waivers)


def test_sdd_waive_remove_restores_finding(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "R",
            "--status",
            "accepted",
        ],
    )
    rid = json.loads(created.stdout)["result"]["id"]
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "waive",
            "add",
            rid,
            "--rule",
            "SDD-REQ-AC",
            "--reason",
            "temp",
        ],
    )
    removed = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "waive",
            "remove",
            rid,
            "--rule",
            "SDD-REQ-AC",
        ],
    )
    assert removed.exit_code == 0, removed.stdout
    assert removed.stdout and json.loads(removed.stdout)["result"]["waivers"] == []
    # sdd check now reports SDD-REQ-AC again.
    checked = runner.invoke(app, ["--root", str(tmp_path), "--json", "sdd", "check"])
    payload = json.loads(checked.stdout)
    data = payload.get("result") or payload["error"]["details"]
    codes = {e["code"] for e in data["errors"]}
    assert "SDD-REQ-AC" in codes


def test_sdd_waive_add_rejects_unknown_rule(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "R"],
    )
    rid = json.loads(created.stdout)["result"]["id"]
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "waive",
            "add",
            rid,
            "--rule",
            "SDD-NOPE",
            "--reason",
            "x",
        ],
    )
    assert result.exit_code != 0


# ---- Phase 3: sdd coverage ----


def test_sdd_coverage_reports_dimensions_and_gaps(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "R",
            "--status",
            "accepted",
        ],
    )
    rp = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(rp)
    metadata["acceptance_criteria"] = [{"statement": "It works."}]
    write_front_matter_document(rp, metadata, BODY)
    # ADR with no traceability (gap)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "adr",
            "ADR",
            "--status",
            "accepted",
        ],
    )
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "coverage"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.sdd-coverage.v1"
    assert payload["totals"]["accepted_requirements"] == 1
    assert payload["totals"]["accepted_adrs"] == 1
    assert payload["coverage"]["accepted_requirements_with_ac"]["covered"] == 1
    assert payload["coverage"]["accepted_adrs_with_traceability"]["covered"] == 0
    assert any("ADR" in g for g in payload["gaps"])


def test_sdd_coverage_include_bdd(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "runtime_scenario",
            "S",
            "--status",
            "accepted",
        ],
    )
    rp = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(rp)
    metadata["bdd"] = {
        "feature": "F",
        "scenario": "S",
        "given": ["g"],
        "when": ["w"],
        "then": ["t"],
        "automation": {"status": "linked", "feature_file": "f.feature"},
    }
    write_front_matter_document(rp, metadata, BODY)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "coverage", "--include-bdd"],
    )
    assert result.exit_code == 0, result.stdout
    cov = json.loads(result.stdout)["result"]["coverage"]
    assert "behavior_with_gwt" in cov
    assert cov["behavior_with_gwt"]["covered"] == 1
    assert cov["behavior_with_feature_file"]["covered"] == 1
    # Option A semantics: linked is not automated.
    assert cov["behavior_linked"]["covered"] == 1
    assert cov["behavior_automated"]["covered"] == 0


def test_sdd_coverage_by_record_lists_per_record_detail(tmp_path: Path) -> None:
    """ac-0008: --by-record emits per-record covered flags and gaps."""
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Uncovered req",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    rid = json.loads(created.stdout)["result"]["id"]

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "coverage", "--by-record"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    rows = payload["by_record"]
    assert rows, "expected at least one by_record row"
    req_row = next(r for r in rows if r["record_id"] == rid)
    assert req_row["type"] == "requirement"
    assert req_row["covered"] == {
        "acceptance_criteria": False,
        "implementation_refs": False,
        "validation": False,
    }
    assert "acceptance_criteria" in req_row["gaps"]

    # Without the flag the list is still present but empty (no per-record work).
    plain = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "coverage"],
    )
    assert plain.exit_code == 0, plain.stdout
    assert json.loads(plain.stdout)["result"]["by_record"] == []


# ---- Phase 3: scoped sdd check ----


def test_sdd_check_scoped_to_record(tmp_path: Path) -> None:
    _init(tmp_path)
    # Record with AC (fewer findings)
    c1 = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "R1",
            "--status",
            "accepted",
        ],
    )
    rid1 = json.loads(c1.stdout)["result"]["id"]
    rp1 = Path(json.loads(c1.stdout)["result"]["path"])
    m1, b1 = read_front_matter_document(rp1)
    m1["acceptance_criteria"] = [{"statement": "ok"}]
    write_front_matter_document(rp1, m1, b1)
    # Record without AC (more findings)
    c2 = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "R2",
            "--status",
            "accepted",
        ],
    )
    rid2 = json.loads(c2.stdout)["result"]["id"]
    # Scoped to rid1: no SDD-REQ-AC
    full = runner.invoke(app, ["--root", str(tmp_path), "--json", "sdd", "check"])
    full_codes = {
        e["code"] for e in json.loads(full.stdout)["error"]["details"]["errors"]
    }
    assert "SDD-REQ-AC" in full_codes  # at least rid2 triggers it
    scoped1 = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check", "--record", rid1],
    )
    s1_payload = json.loads(scoped1.stdout)
    s1_data = s1_payload.get("result") or s1_payload["error"]["details"]
    s1_codes = {e["code"] for e in s1_data["errors"]}
    assert "SDD-REQ-AC" not in s1_codes
    # Scoped to rid2: has SDD-REQ-AC
    scoped2 = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check", "--record", rid2],
    )
    s2_codes = {
        e["code"] for e in json.loads(scoped2.stdout)["error"]["details"]["errors"]
    }
    assert "SDD-REQ-AC" in s2_codes


def test_sdd_check_scoped_to_kind(tmp_path: Path) -> None:
    _init(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "R",
            "--status",
            "accepted",
        ],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "adr",
            "ADR",
            "--status",
            "accepted",
        ],
    )
    # kind=requirement should only surface requirement findings
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check", "--kind", "requirement"],
    )
    payload = json.loads(result.stdout)
    data = payload.get("result") or payload["error"]["details"]
    codes = {e["code"] for e in data["errors"]}
    assert "SDD-REQ-AC" in codes
    assert "SDD-ADR-LINK" not in codes
