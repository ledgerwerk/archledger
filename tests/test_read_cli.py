from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_read_json_includes_current_source_bodies(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
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
        ],
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "read", "--body"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["schema"] == "archledger.read.v1"
    records = payload["result"]["records"]
    black_box = next(item for item in records if item["type"] == "black_box")
    assert black_box["body"].lstrip("\n") == (
        "Describe the purpose and responsibility of this black box.\n"
    )
    assert black_box["body_format"] == "markdown"


def test_read_json_include_draft_flag(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "black-box", "CLI"],
    )

    result_without_drafts = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "read"],
    )
    result_with_drafts = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "read", "--include-drafts"],
    )

    payload_without_drafts = json.loads(result_without_drafts.stdout)
    payload_with_drafts = json.loads(result_with_drafts.stdout)
    assert all(
        item["type"] != "black_box"
        for item in payload_without_drafts["result"]["records"]
    )
    assert any(
        item["type"] == "black_box" for item in payload_with_drafts["result"]["records"]
    )


def test_read_json_filters_by_section(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(app, ["--root", str(tmp_path), "seed", "arc42-minimal"])

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "read", "--section", "building_block_view"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["records"]
    assert all(
        item["section"] == "building_block_view"
        for item in payload["result"]["records"]
    )


def test_read_json_filters_by_kind(tmp_path: Path) -> None:
    init_project(tmp_path)
    runner.invoke(app, ["--root", str(tmp_path), "seed", "arc42-minimal"])

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "read", "--kind", "adr"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["records"]
    assert {item["type"] for item in payload["result"]["records"]} == {"adr"}


def test_read_command_does_not_create_build_output(tmp_path: Path) -> None:
    """Read should not create build output in the project root."""
    init_project(tmp_path, source_format="markdown")
    # Build output dir is "." (project root) by default; read should not create extra files.
    before = set(tmp_path.iterdir())

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "read"])

    assert result.exit_code == 0
    after = set(tmp_path.iterdir())
    # The only new files should be from the .ledger dir (already existing before).
    new_files = after - before
    # No new files at the root level should be created by read.
    assert not any(f.is_file() for f in new_files)


def init_project(tmp_path: Path, source_format: str = "asciidoc") -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", source_format],
    )
    assert result.exit_code == 0
