from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_canonical_config_wins_when_both_exist_and_check_warns(tmp_path: Path) -> None:
    init_project(tmp_path)
    shutil.copy2(tmp_path / "archledger.toml", tmp_path / ".archledger.toml")

    result = runner.invoke(app, ["--root", str(tmp_path), "check"])

    assert result.exit_code == 0
    assert "Both archledger.toml and .archledger.toml exist" in result.stdout


def test_new_black_box_creates_black_box_0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "--title", "CLI"],
    )

    assert result.exit_code == 0
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "building_blocks"
        / "black_box_0001.adoc"
    ).is_file()


def test_new_requirement_creates_requirement_0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "requirement", "--title", "Render output"],
    )

    assert result.exit_code == 0
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "requirements"
        / "requirement_0001.adoc"
    ).is_file()
    created = (
        tmp_path / ".archledger" / "records" / "requirements" / "requirement_0001.adoc"
    ).read_text(encoding="utf-8")
    assert "body_format: asciidoc" in created
    assert "[discrete]\n=== Requirement" in created


def test_new_strategy_item_creates_strategy_item_0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "strategy-item",
            "--title",
            "Keep records canonical",
        ],
    )

    assert result.exit_code == 0
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "strategy"
        / "strategy_item_0001.adoc"
    ).is_file()


def test_new_quality_requirement_creates_quality_requirement_0001(
    tmp_path: Path,
) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "quality-requirement",
            "--title",
            "Deterministic builds",
        ],
    )

    assert result.exit_code == 0
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "quality_requirements"
        / "quality_requirement_0001.adoc"
    ).is_file()


def test_new_context_interface_accepts_context_kind_and_partner(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "context-interface",
            "--title",
            "GitHub",
            "--context-kind",
            "business",
            "--partner",
            "GitHub",
        ],
    )

    assert result.exit_code == 0
    created = (
        tmp_path
        / ".archledger"
        / "records"
        / "contexts"
        / "context_interface_0001.adoc"
    ).read_text(encoding="utf-8")
    assert 'context_kind: "business"' in created
    assert 'partner: "GitHub"' in created


def test_new_infrastructure_accepts_environment(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "infrastructure",
            "--title",
            "Local CLI runtime",
            "--environment",
            "development",
        ],
    )

    assert result.exit_code == 0
    created = (
        tmp_path
        / ".archledger"
        / "records"
        / "deployment"
        / "infrastructure_0001.adoc"
    ).read_text(encoding="utf-8")
    assert 'environment: "development"' in created


def test_new_quality_scenario_accepts_quality_and_environment(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "quality-scenario",
            "--title",
            "Deterministic build",
            "--quality",
            "reproducibility",
            "--environment",
            "ci",
        ],
    )

    assert result.exit_code == 0
    created = (
        tmp_path
        / ".archledger"
        / "records"
        / "quality_scenarios"
        / "quality_scenario_0001.adoc"
    ).read_text(encoding="utf-8")
    assert 'quality: "reproducibility"' in created
    assert 'environment: "ci"' in created


def test_seed_arc42_minimal_creates_starter_records(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "seed", "arc42-minimal"])

    assert result.exit_code == 0
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "building_blocks"
        / "white_box_0001.adoc"
    ).is_file()
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "quality_goals"
        / "quality_goal_0003.adoc"
    ).is_file()
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "decisions"
        / "adr0001.adoc"
    ).is_file()
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "glossary"
        / "glossary_0001.adoc"
    ).is_file()


def test_new_white_box_creates_white_box_0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "white-box", "--title", "Overall System"],
    )

    assert result.exit_code == 0
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "building_blocks"
        / "white_box_0001.adoc"
    ).is_file()


def test_new_adr_creates_adr0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "adr", "--title", "Use Markdown records"],
    )

    assert result.exit_code == 0
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "decisions"
        / "adr0001.adoc"
    ).is_file()


def test_filename_id_must_match(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "--title", "CLI"],
    )
    source = (
        tmp_path
        / ".archledger"
        / "records"
        / "building_blocks"
        / "black_box_0001.adoc"
    )
    renamed = source.with_name("black_box_9999.adoc")
    source.rename(renamed)

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["error"]["details"]["errors"]]
    assert any("does not match filename stem" in message for message in messages)


def test_duplicate_id_check_fails(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "--title", "CLI"],
    )
    original = (
        tmp_path
        / ".archledger"
        / "records"
        / "building_blocks"
        / "black_box_0001.adoc"
    )
    duplicate = (
        tmp_path
        / ".archledger"
        / "records"
        / "concepts"
        / "concept_0001.adoc"
    )
    duplicate.write_text(
        original.read_text(encoding="utf-8").replace(
            "type: black_box",
            "type: concept",
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["error"]["details"]["errors"]]
    assert "Duplicate record ID: black_box_0001" in messages


def test_missing_parent_check_fails(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "black-box",
            "--title",
            "CLI",
            "--parent",
            "white_box_0009",
        ],
    )
    assert result.exit_code == 0

    check_result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert check_result.exit_code == 1
    payload = json.loads(check_result.stdout)
    messages = [item["message"] for item in payload["error"]["details"]["errors"]]
    assert any(
        "Parent reference points to a missing record" in message
        for message in messages
    )


def test_check_warns_for_incomplete_content_metadata(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "quality-goal", "--title", "Reproducibility"],
    )
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "stakeholder", "--title", "Architect"],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "context-interface",
            "--title",
            "GitHub",
            "--context-kind",
            "business",
        ],
    )
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "runtime", "--title", "CLI execution"],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["result"]["warnings"]]
    assert "Quality goal quality_goal_0001 has no scenario." in messages
    assert "Stakeholder stakeholder_0001 has no expectations." in messages
    assert "Context interface context_interface_0001 has no partner." in messages
    assert (
        "Context interface context_interface_0001 has no inputs, outputs, or channels."
        in messages
    )
    assert "Runtime scenario runtime_0001 has no participants." in messages
    assert "Runtime scenario runtime_0001 has no trigger." in messages


def test_check_warns_for_invalid_risk_levels_and_unmeasurable_quality_scenario(
    tmp_path: Path,
) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "risk",
            "--title",
            "Missing template coverage",
        ],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "quality-scenario",
            "--title",
            "Fast build",
            "--quality",
            "reproducibility",
        ],
    )
    risk_path = (
        tmp_path / ".archledger" / "records" / "risks" / "risk_0001.adoc"
    )
    risk_path.write_text(
        risk_path.read_text(encoding="utf-8")
        .replace("severity: medium", "severity: critical")
        .replace("probability: medium", "probability: certain"),
        encoding="utf-8",
    )
    quality_path = (
        tmp_path
        / ".archledger"
        / "records"
        / "quality_scenarios"
        / "quality_scenario_0001.adoc"
    )
    quality_path.write_text(
        quality_path.read_text(encoding="utf-8").replace(
            'response_measure: ""',
            'response_measure: "fast"',
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["result"]["warnings"]]
    assert "Risk risk_0001 has unsupported severity: critical" in messages
    assert "Risk risk_0001 has unsupported probability: certain" in messages
    assert (
        "Quality scenario quality_scenario_0001 response_measure should be measurable."
        in messages
    )


def test_check_strict_fails_on_new_content_warning(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "context-interface", "--title", "GitHub"],
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "check", "--strict"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["error"]["details"]["warnings"]]
    assert "Context interface context_interface_0001 has no partner." in messages


def test_list_excludes_draft_by_default(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "--title", "CLI"],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "list"])

    assert result.exit_code == 0
    assert "No records found." in result.stdout


def test_list_includes_draft_with_flag(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "--title", "CLI"],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "list", "--include-draft"])

    assert result.exit_code == 0
    assert "black_box_0001" in result.stdout


def test_status_human_output(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "status"])

    assert result.exit_code == 0
    assert "Project:" in result.stdout
    assert "Sections:" in result.stdout


def test_status_json_output(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "status"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "status"


def test_new_json_output(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "black-box",
            "--title",
            "CLI",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"]["id"] == "black_box_0001"


def test_new_legacy_v2_project_keeps_markdown_template(tmp_path: Path) -> None:
    init_project(tmp_path)
    (tmp_path / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 2",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[build]",
                'default_output = "architecture.md"',
                "include_draft = false",
                "include_superseded = false",
                "strict = false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "requirement", "--title", "Render output"],
    )

    assert result.exit_code == 0
    created = (
        tmp_path / ".archledger" / "records" / "requirements" / "requirement_0001.md"
    ).read_text(encoding="utf-8")
    assert "body_format: asciidoc" not in created
    assert "## Requirement" in created


def test_show_missing_record_returns_json_error(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "show", "missing"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "show"


def init_project(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert result.exit_code == 0
