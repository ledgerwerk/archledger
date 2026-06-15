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
    assert "version" in schema["required"]
    assert "date" not in schema["properties"]


def test_changed_jsonschema_uses_version_fields(tmp_path: Path) -> None:
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
            "changed",
        ],
    )

    assert result.exit_code == 0
    schema = json.loads(result.stdout)["result"]
    assert schema["properties"]["schema"]["const"] == "archledger.changed.v2"
    assert "version" in schema["properties"]["scan"]["required"]


def test_schema_target_sdd_fails(tmp_path: Path) -> None:
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
            "sdd",
        ],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert "schema target must be one of:" in payload["error"]["message"]


def test_schema_target_bdd_export_fails(tmp_path: Path) -> None:
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
            "bdd-export",
        ],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert "schema target must be one of:" in payload["error"]["message"]


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
    assert "Refusing to overwrite" in second.output
    assert forced.exit_code == 0, forced.stdout


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout
