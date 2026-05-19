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
        / "black_box_0001.md"
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
        / "white_box_0001.md"
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
        / "adr0001.md"
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
        / "black_box_0001.md"
    )
    renamed = source.with_name("black_box_9999.md")
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
        / "black_box_0001.md"
    )
    duplicate = (
        tmp_path
        / ".archledger"
        / "records"
        / "concepts"
        / "concept_0001.md"
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
