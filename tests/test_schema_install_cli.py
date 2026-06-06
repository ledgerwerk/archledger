from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_schema_jsonschema_target_is_returned(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "schema",
            "--format",
            "jsonschema",
            "--target",
            "record",
        ],
    )

    assert result.exit_code == 0, result.stdout
    schema = json.loads(result.stdout)["result"]
    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["title"] == "Archledger record front matter"


def test_install_refuses_overwrite_without_force(tmp_path: Path) -> None:
    _init(tmp_path)
    first = runner.invoke(
        app,
        ["--root", str(tmp_path), "install", "pr-template"],
    )
    second = runner.invoke(
        app,
        ["--root", str(tmp_path), "install", "pr-template"],
    )
    forced = runner.invoke(
        app,
        ["--root", str(tmp_path), "install", "pr-template", "--force"],
    )

    assert first.exit_code == 0, first.stdout
    assert second.exit_code == 1
    assert "Refusing to overwrite" in second.stderr
    assert forced.exit_code == 0, forced.stdout


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout
