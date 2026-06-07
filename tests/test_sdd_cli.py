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
    assert payload["profile_enabled"] is True


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
