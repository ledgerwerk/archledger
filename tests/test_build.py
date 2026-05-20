from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_build_generates_all_arc42_major_sections(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / ".archledger" / "build" / "architecture.adoc").read_text(
        encoding="utf-8"
    )
    assert "== Introduction and Goals" in output
    assert "== Architecture Constraints" in output
    assert "== Context and Scope" in output
    assert "== Building Block View" in output
    assert "=== Requirements Overview" in output
    assert "=== Quality Goals" in output
    assert "=== Stakeholders" in output
    assert "=== Business Context" in output
    assert "=== Technical Context" in output
    assert "=== Strategy Items" in output
    assert "=== Quality Requirements Overview" in output
    assert "=== Quality Scenarios" in output
    assert "== Glossary" in output


def test_build_includes_structured_arc42_sections(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "white-box",
            "--title",
            "Overall System",
            "--status",
            "accepted",
        ],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "requirement",
            "--title",
            "Render architecture document from AsciiDoc records",
            "--status",
            "accepted",
        ],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "strategy-item",
            "--title",
            "Keep records as canonical source",
            "--status",
            "accepted",
        ],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "quality-requirement",
            "--title",
            "Deterministic builds",
            "--status",
            "accepted",
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
            "Stable architecture build",
            "--status",
            "accepted",
            "--quality",
            "reproducibility",
        ],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "context-interface",
            "--title",
            "Business partner",
            "--status",
            "accepted",
            "--context-kind",
            "business",
            "--partner",
            "Business partner",
        ],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "context-interface",
            "--title",
            "Technical integration",
            "--status",
            "accepted",
            "--context-kind",
            "technical",
            "--partner",
            "Technical integration",
        ],
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "black-box",
            "--title",
            "CLI",
            "--status",
            "accepted",
            "--parent",
            "white_box_0001",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / ".archledger" / "build" / "architecture.adoc").read_text(
        encoding="utf-8"
    )
    assert "=== Whitebox Overall System" in output
    assert "==== Level 1" in output
    assert "===== CLI" in output
    assert "=== Strategy Items" in output
    assert "=== Quality Requirements Overview" in output
    assert "=== Business Context" in output
    assert "=== Technical Context" in output


def test_build_includes_adr_under_architecture_decisions(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "adr",
            "--title",
            "Use AsciiDoc records",
            "--status",
            "accepted",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / ".archledger" / "build" / "architecture.adoc").read_text(
        encoding="utf-8"
    )
    assert "== Architecture Decisions" in output
    assert "Use AsciiDoc records" in output
    assert "*Status:* accepted" in output
    assert "*Deciders:*" in output


def test_build_renders_structured_risk_overview(tmp_path: Path) -> None:
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
            "--status",
            "accepted",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / ".archledger" / "build" / "architecture.adoc").read_text(
        encoding="utf-8"
    )
    assert "== Risks and Technical Debt" in output
    assert "=== Risk Overview" in output
    assert "|Title |Severity |Probability |Mitigation |Notes" in output


def test_build_is_deterministic(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "white-box",
            "--title",
            "Overall System",
            "--status",
            "accepted",
        ],
    )

    first = runner.invoke(app, ["--root", str(tmp_path), "build"])
    output_path = tmp_path / ".archledger" / "build" / "architecture.adoc"
    first_output = output_path.read_text(encoding="utf-8")
    second = runner.invoke(app, ["--root", str(tmp_path), "build"])
    second_output = output_path.read_text(encoding="utf-8")

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first_output == second_output


def test_build_output_path_can_be_overridden(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "build", "--output", "docs/architecture.adoc"],
    )

    assert result.exit_code == 0
    assert (tmp_path / "docs" / "architecture.adoc").is_file()


def test_build_strict_fails_on_check_warning(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "build", "--strict"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "build"


def test_build_json_output(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "build"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "build"


def test_legacy_markdown_project_still_builds_markdown(tmp_path: Path) -> None:
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
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "requirement",
            "--title",
            "Render markdown output",
            "--status",
            "accepted",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / ".archledger" / "build" / "architecture.md").read_text(
        encoding="utf-8"
    )
    assert "# Introduction and Goals" in output
    assert "Render markdown output" in output


def init_project(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert result.exit_code == 0
