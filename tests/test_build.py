from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_build_generates_all_arc42_major_sections(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / "build" / "architecture.adoc").read_text(encoding="utf-8")
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
            "CLI",
            "--status",
            "accepted",
            "--parent",
            "al_0013",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / "build" / "architecture.adoc").read_text(encoding="utf-8")
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
            "Use AsciiDoc records",
            "--status",
            "accepted",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / "build" / "architecture.adoc").read_text(encoding="utf-8")
    assert "== Architecture Decisions" in output
    assert "Use AsciiDoc records" in output
    assert "*Status:* accepted" in output
    assert "*Deciders:*" in output


def test_build_includes_diagram_records_in_runtime_view(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "diagram",
            "Runtime login flow",
            "--status",
            "accepted",
            "--section",
            "runtime_view",
            "--caption",
            "Runtime login flow",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / "build" / "architecture.adoc").read_text(encoding="utf-8")
    assert "== Runtime View" in output
    assert "=== Runtime login flow" in output
    assert "[source,text]" in output
    assert "*Caption:* Runtime login flow" in output


def test_build_renders_structured_risk_overview(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "risk",
            "Missing template coverage",
            "--status",
            "accepted",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / "build" / "architecture.adoc").read_text(encoding="utf-8")
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
            "Overall System",
            "--status",
            "accepted",
        ],
    )

    first = runner.invoke(app, ["--root", str(tmp_path), "build"])
    output_path = tmp_path / "build" / "architecture.adoc"
    first_output = output_path.read_text(encoding="utf-8")
    second = runner.invoke(app, ["--root", str(tmp_path), "build"])
    second_output = output_path.read_text(encoding="utf-8")

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first_output == second_output


def test_build_uses_source_date_epoch_for_document_date(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "build"],
        env={"SOURCE_DATE_EPOCH": "946684800"},
    )

    assert result.exit_code == 0
    output = (tmp_path / "build" / "architecture.adoc").read_text(encoding="utf-8")
    assert ":revdate: 2000-01-01" in output


def test_build_uses_latest_record_metadata_date_when_epoch_not_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "requirement",
            "Date anchor requirement",
            "--status",
            "accepted",
        ],
    )
    record_path = tmp_path / ".archledger" / "records" / "requirements" / "al_0013.adoc"
    lines = record_path.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    for line in lines:
        if line.startswith("date: "):
            updated_lines.append('date: "2042-12-31"')
            continue
        if line.startswith("updated_at: "):
            updated_lines.append('updated_at: "2042-12-31T23:59:59Z"')
            continue
        updated_lines.append(line)
    record_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / "build" / "architecture.adoc").read_text(encoding="utf-8")
    assert ":revdate: 2042-12-31" in output


def test_build_output_path_can_be_overridden(tmp_path: Path) -> None:
    init_project(tmp_path)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "build", "--output", "docs/architecture.adoc"],
    )

    assert result.exit_code == 0
    assert (tmp_path / "docs" / "architecture.adoc").is_file()


def test_build_respects_default_output_dir(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'default_output_dir = "build"',
            'default_output_dir = "site-build"',
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    assert (tmp_path / "site-build" / "architecture.adoc").is_file()
    assert not (tmp_path / ".archledger" / "site-build" / "architecture.adoc").exists()


def test_hidden_config_default_output_dir_dot_writes_to_config_dir(
    tmp_path: Path,
) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", "markdown"],
    )
    assert result.exit_code == 0, result.stdout

    config_path = tmp_path / "archledger.toml"
    hidden_config_path = tmp_path / ".archledger.toml"

    config_text = config_path.read_text(encoding="utf-8")
    config_text = config_text.replace(
        'default_output = "architecture.md"',
        'default_output = "ARCHITECTURE.md"',
    )
    config_text = config_text.replace(
        'default_output_dir = "build"',
        'default_output_dir = "."',
    )

    hidden_config_path.write_text(config_text, encoding="utf-8")
    config_path.unlink()

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "requirement",
            "Export root architecture document",
            "--status",
            "accepted",
        ],
    )
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])
    assert result.exit_code == 0, result.stdout

    assert (tmp_path / "ARCHITECTURE.md").is_file()
    assert not (tmp_path / ".archledger" / "ARCHITECTURE.md").exists()


def test_build_respects_default_output_filename(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'default_output = "architecture.adoc"',
            'default_output = "custom-architecture.adoc"',
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    assert (tmp_path / "build" / "custom-architecture.adoc").is_file()
    assert not (tmp_path / "build" / "architecture.adoc").exists()


def test_explicit_output_overrides_configured_default_output(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'default_output = "architecture.adoc"',
            'default_output = "custom-architecture.adoc"',
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "build", "--output", "docs/architecture.adoc"],
    )

    assert result.exit_code == 0
    assert (tmp_path / "docs" / "architecture.adoc").is_file()
    assert not (tmp_path / "build" / "custom-architecture.adoc").exists()


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
            "Render markdown output",
            "--status",
            "accepted",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / "build" / "architecture.md").read_text(encoding="utf-8")
    assert "# Introduction and Goals" in output
    assert "Render markdown output" in output


def init_project(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["--root", str(tmp_path), "init", "--source-format", "asciidoc"]
    )
    assert result.exit_code == 0
