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
    output = (tmp_path / ".archledger" / "build" / "architecture.md").read_text(
        encoding="utf-8"
    )
    assert "# Introduction and Goals" in output
    assert "# Architecture Constraints" in output
    assert "# Context and Scope" in output
    assert "# Building Block View" in output
    assert "# Glossary" in output


def test_build_includes_black_box_under_building_block_view(tmp_path: Path) -> None:
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
    output = (tmp_path / ".archledger" / "build" / "architecture.md").read_text(
        encoding="utf-8"
    )
    assert "# Building Block View" in output
    assert "CLI" in output


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
            "Use Markdown records",
            "--status",
            "accepted",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
    output = (tmp_path / ".archledger" / "build" / "architecture.md").read_text(
        encoding="utf-8"
    )
    assert "# Architecture Decisions" in output
    assert "Use Markdown records" in output


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
    output_path = tmp_path / ".archledger" / "build" / "architecture.md"
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
        ["--root", str(tmp_path), "build", "--output", "docs/architecture.md"],
    )

    assert result.exit_code == 0
    assert (tmp_path / "docs" / "architecture.md").is_file()


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


def init_project(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert result.exit_code == 0
