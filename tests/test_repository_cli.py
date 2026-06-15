from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.paths import resolve_project_paths
from archledger.storage.source_state import read_source_state

runner = CliRunner()


def test_canonical_config_wins_when_both_exist_and_check_warns(tmp_path: Path) -> None:
    init_project(tmp_path)
    shutil.copy2(tmp_path / "archledger.toml", tmp_path / ".archledger.toml")

    result = runner.invoke(app, ["--root", str(tmp_path), "check"])

    assert result.exit_code == 0
    assert "Both archledger.toml and .archledger.toml exist" in result.stdout


def test_snapshot_writes_source_state_json(tmp_path: Path) -> None:
    init_project(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("print('hello')\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "source",
            "snapshot",
            "--reason",
            "after-archledger-update",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["schema"] == "archledger.snapshot.v2"
    paths, _, _ = resolve_project_paths(tmp_path)
    state = read_source_state(paths.source_state_path)
    assert state is not None
    assert state.schema == "archledger.source-state.v3"
    assert state.version == 1
    assert "src/module.py" in state.files
    assert "." in state.directories


def test_snapshot_respects_tracking_disabled(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "[tracking]\nenabled = true",
            "[tracking]\nenabled = false",
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "source", "snapshot"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "tracking is disabled" in payload["error"]["message"].lower()
    assert not (tmp_path / ".archledger" / "source-state.json").exists()


def test_changed_json_is_stable_without_baseline(tmp_path: Path) -> None:
    init_project(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("print('hello')\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "source", "changed"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["schema"] == "archledger.changed.v2"
    assert payload["result"]["baseline"]["exists"] is False
    assert "src/module.py" in payload["result"]["changes"]["unbaselined_files"]


def test_changed_respects_tracking_disabled(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "[tracking]\nenabled = true",
            "[tracking]\nenabled = false",
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "source", "changed"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "tracking is disabled" in payload["error"]["message"].lower()


def test_changed_json_reports_modified_file_and_impacted_record(tmp_path: Path) -> None:
    init_project(tmp_path)
    (tmp_path / "src").mkdir()
    source_path = tmp_path / "src" / "module.py"
    source_path.write_text("print('v1')\n", encoding="utf-8")
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "white-box",
            "Tracking layer",
            "--status",
            "proposed",
        ],
    )
    record_path = (
        tmp_path / ".archledger" / "records" / "building_blocks" / "block-0013.adoc"
    )
    record_path.write_text(
        record_path.read_text(encoding="utf-8").replace(
            "\n---\n\n",
            "\nsource_refs:\n  - src/module.py#module\n---\n\n",
            1,
        ),
        encoding="utf-8",
    )
    snapshot_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "source",
            "snapshot",
            "--reason",
            "baseline",
        ],
    )
    assert snapshot_result.exit_code == 0

    source_path.write_text("print('v2')\n", encoding="utf-8")
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "source", "changed", "--include-drafts"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["result"]
    assert payload["baseline"]["exists"] is True
    assert payload["changes"]["modified"][0]["path"] == "src/module.py"
    assert payload["changes"]["modified"][0]["change"] == "modified"
    assert "old_sha256" in payload["changes"]["modified"][0]
    assert "new_sha256" in payload["changes"]["modified"][0]
    assert "size" not in payload["changes"]["modified"][0]
    assert payload["impact"]["records"][0]["id"] == "block-0013"
    assert payload["impact"]["records"][0]["matched_refs"] == ["src/module.py"]
    assert "building_block_view" in payload["impact"]["sections"]


def test_new_black_box_creates_black_box_0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "CLI"],
    )

    assert result.exit_code == 0
    assert (
        tmp_path / ".archledger" / "records" / "building_blocks" / "block-0013.adoc"
    ).is_file()


def test_new_requirement_creates_requirement_0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "requirement", "Render output"],
    )

    assert result.exit_code == 0
    assert (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    ).is_file()
    created = (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    ).read_text(encoding="utf-8")
    assert "body_format: asciidoc" in created
    assert "[discrete]\n=== Requirement" in created


def test_new_record_uses_configured_id_format(tmp_path: Path) -> None:
    init_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--source-format",
            "markdown",
            "--id-prefix",
            "ta",
            "--id-width",
            "3",
        ],
    )
    assert init_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Local accounting",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["id"] == "content-013"
    assert payload["result"]["path"].endswith("records/requirements/content-013.md")


def test_new_requirement_uses_content_segment_when_enabled(tmp_path: Path) -> None:
    init_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--source-format",
            "markdown",
            "--id-segment-mode",
            "type",
        ],
    )
    assert init_result.exit_code == 0, init_result.stdout

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Local accounting",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["id"] == "content-0013"
    assert payload["result"]["path"].endswith("records/requirements/content-0013.md")


def test_new_risk_uses_risk_segment_when_enabled(tmp_path: Path) -> None:
    init_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--source-format",
            "markdown",
            "--id-segment-mode",
            "type",
        ],
    )
    assert init_result.exit_code == 0, init_result.stdout

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "risk",
            "Data retention risk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["id"] == "risk-0013"
    assert payload["result"]["path"].endswith("records/risks/risk-0013.md")


def test_new_requirement_increments_with_custom_record_extension(
    tmp_path: Path,
) -> None:
    init_result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", "markdown"],
    )
    assert init_result.exit_code == 0, init_result.stdout
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'record_extension = ".md"',
            'record_extension = ".mk"',
        ),
        encoding="utf-8",
    )

    for title in ["A", "B", "C"]:
        result = runner.invoke(
            app,
            [
                "--root",
                str(tmp_path),
                "new",
                "requirement",
                title,
                "--status",
                "accepted",
            ],
        )
        assert result.exit_code == 0, result.stdout

    record_dir = tmp_path / ".archledger" / "records" / "requirements"
    assert sorted(path.name for path in record_dir.iterdir()) == [
        "content-0013.mk",
        "content-0014.mk",
        "content-0015.mk",
    ]
    assert 'title: "C"' in (record_dir / "content-0015.mk").read_text(encoding="utf-8")
    assert "next_number: 16" in (tmp_path / ".archledger" / "storage.yaml").read_text(
        encoding="utf-8"
    )


def test_new_strategy_item_creates_strategy_item_0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "strategy-item",
            "Keep records canonical",
        ],
    )

    assert result.exit_code == 0
    assert (
        tmp_path / ".archledger" / "records" / "strategy" / "strategy-0013.adoc"
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
            "Deterministic builds",
        ],
    )

    assert result.exit_code == 0
    assert (
        tmp_path
        / ".archledger"
        / "records"
        / "quality_requirements"
        / "quality-0013.adoc"
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
            "GitHub",
            "--context-kind",
            "business",
            "--partner",
            "GitHub",
        ],
    )

    assert result.exit_code == 0
    created = (
        tmp_path / ".archledger" / "records" / "contexts" / "context-0013.adoc"
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
            "Local CLI runtime",
            "--environment",
            "development",
        ],
    )

    assert result.exit_code == 0
    created = (
        tmp_path / ".archledger" / "records" / "deployment" / "deploy-0013.adoc"
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
            "Deterministic build",
            "--quality",
            "reproducibility",
            "--environment",
            "ci",
        ],
    )

    assert result.exit_code == 0
    created = (
        tmp_path / ".archledger" / "records" / "quality_scenarios" / "quality-0013.adoc"
    ).read_text(encoding="utf-8")
    assert 'quality: "reproducibility"' in created
    assert 'environment: "ci"' in created


def test_new_diagram_accepts_diagram_options(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "diagram",
            "Runtime login flow",
            "--section",
            "runtime_view",
            "--diagram-type",
            "mermaid",
            "--caption",
            "Runtime login flow",
            "--related",
            "al_0040",
            "--related",
            "al_0041",
        ],
    )

    assert result.exit_code == 0
    created = (
        tmp_path / ".archledger" / "records" / "diagrams" / "diagram-0013.adoc"
    ).read_text(encoding="utf-8")
    assert 'diagram_type: "mermaid"' in created
    assert 'caption: "Runtime login flow"' in created
    assert "related_records:" in created
    assert '"al_0040"' in created
    assert '"al_0041"' in created
    assert "[mermaid]" in created


def test_seed_arc42_minimal_creates_starter_records(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "seed", "arc42-minimal"])

    assert result.exit_code == 0
    assert (
        tmp_path / ".archledger" / "records" / "building_blocks" / "block-0013.adoc"
    ).is_file()
    assert (
        tmp_path / ".archledger" / "records" / "quality_goals" / "quality-0016.adoc"
    ).is_file()
    assert (
        tmp_path / ".archledger" / "records" / "decisions" / "adr-0021.adoc"
    ).is_file()
    assert (
        tmp_path / ".archledger" / "records" / "glossary" / "glossary-0023.adoc"
    ).is_file()


def test_new_white_box_creates_white_box_0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "white-box", "Overall System"],
    )

    assert result.exit_code == 0
    assert (
        tmp_path / ".archledger" / "records" / "building_blocks" / "block-0013.adoc"
    ).is_file()


def test_new_adr_creates_adr0001(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "adr", "Use Markdown records"],
    )

    assert result.exit_code == 0
    assert (
        tmp_path / ".archledger" / "records" / "decisions" / "adr-0013.adoc"
    ).is_file()


def test_filename_id_must_match(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "CLI"],
    )
    source = (
        tmp_path / ".archledger" / "records" / "building_blocks" / "block-0013.adoc"
    )
    renamed = source.with_name("al_9999.adoc")
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
        ["--root", str(tmp_path), "new", "black-box", "CLI"],
    )
    original = (
        tmp_path / ".archledger" / "records" / "building_blocks" / "block-0013.adoc"
    )
    duplicate = tmp_path / ".archledger" / "records" / "concepts" / "concept_0001.adoc"
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
    assert "Duplicate record ID: block-0013" in messages


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
            "CLI",
            "--parent",
            "al_0099",
        ],
    )
    assert result.exit_code == 0

    check_result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert check_result.exit_code == 1
    payload = json.loads(check_result.stdout)
    messages = [item["message"] for item in payload["error"]["details"]["errors"]]
    assert any(
        "Parent reference points to a missing record" in message for message in messages
    )


def test_check_warns_for_incomplete_content_metadata(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "quality-goal", "Reproducibility"],
    )
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "stakeholder", "Architect"],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "context-interface",
            "GitHub",
            "--context-kind",
            "business",
        ],
    )
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "runtime", "CLI execution"],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["result"]["warnings"]]
    assert "Quality goal quality-0013 has no scenario." in messages
    assert "Stakeholder content-0014 has no expectations." in messages
    assert "Context interface context-0015 has no partner." in messages
    assert (
        "Context interface context-0015 has no inputs, outputs, or channels."
        in messages
    )
    assert "Runtime scenario runtime-0016 has no participants." in messages
    assert "Runtime scenario runtime-0016 has no trigger." in messages


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
            "Fast build",
            "--quality",
            "reproducibility",
        ],
    )
    risk_path = tmp_path / ".archledger" / "records" / "risks" / "risk-0013.adoc"
    risk_path.write_text(
        risk_path.read_text(encoding="utf-8")
        .replace("severity: medium", "severity: critical")
        .replace("probability: medium", "probability: certain"),
        encoding="utf-8",
    )
    quality_path = (
        tmp_path / ".archledger" / "records" / "quality_scenarios" / "quality-0014.adoc"
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
    assert "Risk risk-0013 has unsupported severity: critical" in messages
    assert "Risk risk-0013 has unsupported probability: certain" in messages
    assert (
        "Quality scenario quality-0014 response_measure should be measurable."
        in messages
    )


def test_check_strict_fails_on_new_content_warning(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "context-interface", "GitHub"],
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "check", "--strict"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["error"]["details"]["warnings"]]
    assert "Context interface context-0013 has no partner." in messages


def test_check_warns_for_invalid_source_ref_path_traversal(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "white-box", "Tracking layer"],
    )
    record_path = (
        tmp_path / ".archledger" / "records" / "building_blocks" / "block-0013.adoc"
    )
    record_path.write_text(
        record_path.read_text(encoding="utf-8").replace(
            "\n---\n\n",
            "\nsource_refs:\n  - ../secret.py\n---\n\n",
            1,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["result"]["warnings"]]
    assert (
        "Record block-0013 source_refs entry 1 path must not contain '..':"
        " ../secret.py" in messages
    )


def test_check_warns_for_missing_directory_source_ref(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "white-box", "Tracking layer"],
    )
    record_path = (
        tmp_path / ".archledger" / "records" / "building_blocks" / "block-0013.adoc"
    )
    record_path.write_text(
        record_path.read_text(encoding="utf-8").replace(
            "\n---\n\n",
            "\nsource_refs:\n  - missing_dir/\n---\n\n",
            1,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    messages = [
        item["message"]
        for item in payload["result"]["warnings"] + payload["result"]["errors"]
    ]
    assert any(
        "directory does not exist: missing_dir/" in message for message in messages
    )


def test_check_warns_for_backslash_source_ref_path(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "white-box", "Tracking layer"],
    )
    record_path = (
        tmp_path / ".archledger" / "records" / "building_blocks" / "block-0013.adoc"
    )
    record_path.write_text(
        record_path.read_text(encoding="utf-8").replace(
            "\n---\n\n",
            "\nsource_refs:\n  - src\\module.py\n---\n\n",
            1,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["result"]["warnings"]]
    assert (
        "Record block-0013 source_refs entry 1 path must use POSIX separators:"
        " src\\module.py" in messages
    )


def test_list_excludes_draft_by_default(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "CLI"],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "list"])

    assert result.exit_code == 0
    assert "No records found." in result.stdout


def test_list_includes_draft_with_flag(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "CLI"],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "list", "--include-drafts"])

    assert result.exit_code == 0
    assert "block-0013" in result.stdout


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
    assert payload["result"]["archive_dir"].endswith(".archledger/archive")


def test_paths_json_includes_archive_and_source_state_path(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "paths"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"]["archive_dir"].endswith(".archledger/archive")
    assert payload["result"]["source_state_path"].endswith(
        ".archledger/source-state.json"
    )


def test_check_rejects_removed_fix_option(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "check", "--fix"])

    assert result.exit_code != 0
    assert "No such option" in result.output


def test_source_group_help_lists_snapshot_changed_convert() -> None:
    result = runner.invoke(app, ["source", "--help"])

    assert result.exit_code == 0
    assert "snapshot" in result.stdout
    assert "changed" in result.stdout
    assert "convert" in result.stdout


def test_visibility_all_statuses_includes_drafts_and_superseded(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(app, ["--root", str(tmp_path), "new", "black-box", "Draft CLI"])
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "black-box",
            "Old CLI",
            "--status",
            "superseded",
        ],
    )

    default_result = runner.invoke(app, ["--root", str(tmp_path), "--json", "read"])
    all_statuses_result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "read", "--all-statuses"],
    )

    assert default_result.exit_code == 0
    assert all_statuses_result.exit_code == 0
    default_records = json.loads(default_result.stdout)["result"]["records"]
    all_statuses_records = json.loads(all_statuses_result.stdout)["result"]["records"]
    default_titles = {item["title"] for item in default_records}
    all_titles = {item["title"] for item in all_statuses_records}
    assert "Draft CLI" not in default_titles
    assert "Old CLI" not in default_titles
    assert "Draft CLI" in all_titles
    assert "Old CLI" in all_titles


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
            "CLI",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"]["id"] == "block-0013"


def test_new_diagram_json_output(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "diagram",
            "Deployment topology",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"]["id"] == "diagram-0013"
    assert payload["result"]["path"].endswith("records/diagrams/diagram-0013.adoc")


def test_new_legacy_v2_project_keeps_markdown_template(tmp_path: Path) -> None:
    import shutil

    init_project(tmp_path)
    # Move sections from profile location to legacy location for v2 config.
    profile_sections = tmp_path / ".archledger" / "profiles" / "arc42" / "sections"
    legacy_sections = tmp_path / ".archledger" / "sections"
    if profile_sections.is_dir() and not legacy_sections.is_dir():
        shutil.move(str(profile_sections), str(legacy_sections))
        profile_arc42 = tmp_path / ".archledger" / "profiles" / "arc42"
        if profile_arc42.is_dir():
            shutil.rmtree(str(profile_arc42))
        profiles_root = tmp_path / ".archledger" / "profiles"
        if profiles_root.is_dir() and not any(profiles_root.iterdir()):
            profiles_root.rmdir()
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
        ["--root", str(tmp_path), "new", "requirement", "Render output"],
    )

    assert result.exit_code == 0
    created = (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.md"
    ).read_text(encoding="utf-8")
    assert "body_format: markdown" in created
    assert "schema_version: 4" in created
    assert "version: 1" in created
    assert "## Requirement" in created


def test_show_missing_record_returns_json_error(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "show", "missing"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "show"


def test_archive_moves_record_to_archive_and_excludes_from_list(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "requirement",
            "Old requirement",
            "--status",
            "accepted",
        ],
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "archive", "content-0013", "--reason", "obsolete"],
    )

    assert result.exit_code == 0
    active_record = (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    )
    assert not active_record.exists()
    archived = (
        tmp_path
        / ".archledger"
        / "archive"
        / "records"
        / "requirements"
        / "content-0013.adoc"
    )
    assert archived.is_file()
    text = archived.read_text(encoding="utf-8")
    assert "status: archived" in text
    assert "archived_reason: obsolete" in text

    list_result = runner.invoke(
        app,
        ["--root", str(tmp_path), "list", "--all-statuses"],
    )
    assert "content-0013" not in list_result.stdout


def test_new_record_does_not_reuse_archived_number(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "Old"])
    runner.invoke(app, ["--root", str(tmp_path), "archive", "content-0013"])
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "New"])

    new_record_path = (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0014.adoc"
    )
    assert new_record_path.is_file()


def test_check_fails_when_ledger_number_is_missing(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "B"])

    (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    ).unlink()

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["error"]["details"]["errors"]]
    assert any("Missing ledger ID: <kind>-0013" in message for message in messages)


def test_doctor_repair_creates_tombstone_for_missing_record_number(
    tmp_path: Path,
) -> None:
    init_project(tmp_path)
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])
    missing = (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    )
    missing.unlink()

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "doctor", "--repair"],
    )

    assert result.exit_code == 0
    tombstone = (
        tmp_path / ".archledger" / "archive" / "tombstones" / "archive-0013.adoc"
    )
    assert tombstone.is_file()
    payload = json.loads(result.stdout)
    repairs = payload["result"]["repairs"]
    assert any(item["kind"] == "created_tombstone" for item in repairs)


def test_doctor_repair_refuses_duplicate_ids(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])
    original = (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    )
    duplicate = (
        tmp_path
        / ".archledger"
        / "archive"
        / "records"
        / "requirements"
        / "content-0013.adoc"
    )
    duplicate.parent.mkdir(parents=True)
    duplicate.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "doctor", "--repair"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert any(
        "Duplicate ledger ID <kind>-0013" in item["message"]
        for item in payload["error"]["details"]["errors"]
    )


def test_new_refuses_to_allocate_when_storage_counter_proves_missing_number(
    tmp_path: Path,
) -> None:
    init_project(tmp_path)
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])
    path = tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    path.unlink()

    result = runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "B"])

    assert result.exit_code == 1
    assert "doctor --repair" in result.output


def test_doctor_repair_recreates_missing_required_section(tmp_path: Path) -> None:
    init_project(tmp_path)
    section = (
        tmp_path
        / ".archledger"
        / "profiles"
        / "arc42"
        / "sections"
        / "content-0002.adoc"
    )
    section.unlink()

    result = runner.invoke(app, ["--root", str(tmp_path), "doctor", "--repair"])

    assert result.exit_code == 0
    assert section.is_file()
    tombstone = (
        tmp_path / ".archledger" / "archive" / "tombstones" / "content-0002.adoc"
    )
    assert not tombstone.exists()


def init_project(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["--root", str(tmp_path), "init", "--source-format", "asciidoc"]
    )
    assert result.exit_code == 0


def test_doctor_repair_refuses_legacy_ids_before_migration(tmp_path: Path) -> None:
    init_project(tmp_path)

    # Remove current local-ID files and replace one with legacy form.
    sections_dir = tmp_path / ".archledger" / "profiles" / "arc42" / "sections"
    for path in sections_dir.glob("*.adoc"):
        path.unlink()
    legacy = sections_dir / "al_0001.adoc"
    legacy.write_text(
        "---\n"
        "schema_version: 2\n"
        "id: al_0001\n"
        "type: section\n"
        "title: Introduction and Goals\n"
        "status: accepted\n"
        "section: introduction_and_goals\n"
        "order: 10\n"
        "body_format: asciidoc\n"
        "---\n\nLegacy section.\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "doctor", "--repair"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    messages = [item["message"] for item in payload["error"]["details"]["errors"]]
    assert any("migrate ids --to ledgercore --apply" in message for message in messages)

    assert not list(
        (tmp_path / ".archledger" / "archive" / "tombstones").glob("*.adoc")
    )


def test_check_tolerates_legacy_profiles_sdd_table(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + '\n[profiles.sdd]\nkind = "contract"\nrequire_test_refs = true\n',
        encoding="utf-8",
    )

    checked = runner.invoke(app, ["--root", str(tmp_path), "check"])
    assert checked.exit_code == 0, checked.stdout
