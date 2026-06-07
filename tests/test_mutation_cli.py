from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_nested_mutation_commands_update_record(tmp_path: Path) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "Feature"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    body = tmp_path / "body.md"
    body.write_text("More detail.\n", encoding="utf-8")

    commands = [
        ["record", "set", record_id, "--status", "proposed"],
        ["record", "meta", "set", record_id, "priority", "must"],
        ["record", "body", "append", record_id, "--file", str(body)],
        ["refs", "add", record_id, "--path", "src/feature.py", "--role", "implements"],
        ["ac", "add", record_id, "--statement", "Feature works"],
    ]
    for command in commands:
        result = runner.invoke(app, ["--root", str(tmp_path), *command])
        assert result.exit_code == 0, result.stdout

    text = record_path.read_text(encoding="utf-8")
    assert "status: proposed" in text
    assert "priority: must" in text
    assert "More detail." in text
    assert "role: implements" in text
    assert "Feature works" in text


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout


def test_record_body_set_replaces_body_and_validates_record(tmp_path: Path) -> None:
    """P0: record body set replaces (not appends) the body and revalidates."""
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "R"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    body_file = tmp_path / "new_body.md"
    body_file.write_text("# Replaced body\n\nReal content.\n", encoding="utf-8")
    # The template placeholder snippet must be replaced.
    from archledger.checks import PLACEHOLDER_SNIPPETS

    before = record_path.read_text(encoding="utf-8")
    assert any(snip in before for snip in PLACEHOLDER_SNIPPETS)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "body",
            "set",
            record_id,
            "--from-file",
            str(body_file),
        ],
    )
    assert result.exit_code == 0, result.stdout
    after = record_path.read_text(encoding="utf-8")
    assert "# Replaced body" in after
    assert "Real content." in after
    for snip in PLACEHOLDER_SNIPPETS:
        assert snip not in after, f"placeholder {snip!r} still present after set"


def test_record_body_set_text_replaces_body(tmp_path: Path) -> None:
    """record body set --text replaces the body inline."""
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "R"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "body",
            "set",
            record_id,
            "--text",
            "Inline replacement body.",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Inline replacement body." in record_path.read_text(encoding="utf-8")
