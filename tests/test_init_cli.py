from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.project_config import normalize_project_name

runner = CliRunner()


def test_init_writes_archledger_toml_and_default_storage(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])

    assert result.exit_code == 0
    assert (tmp_path / "archledger.toml").is_file()
    assert (tmp_path / ".archledger" / "storage.yaml").is_file()
    assert (tmp_path / ".archledger" / "sections").is_dir()
    assert (tmp_path / ".archledger" / "records" / "building_blocks").is_dir()
    assert (
        tmp_path / ".archledger" / "sections" / "01_introduction_and_goals.adoc"
    ).is_file()
    storage_text = (tmp_path / ".archledger" / "storage.yaml").read_text(
        encoding="utf-8"
    )
    assert "requirement: 1" in storage_text
    assert "strategy_item: 1" in storage_text
    assert "quality_requirement: 1" in storage_text


def test_init_project_name_defaults_to_workspace_basename(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])

    assert result.exit_code == 0
    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert "config_version = 3" in config_text
    assert "[source]" in config_text
    assert 'format = "asciidoc"' in config_text
    assert 'section_extension = ".adoc"' in config_text
    assert f'project_name = "{normalize_project_name(tmp_path.name)}"' in config_text
    assert "include_superseded = false" in config_text
    assert "[skill]" in config_text


def test_init_project_name_option_overrides_basename(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--project-name", "My Cool App"],
    )

    assert result.exit_code == 0
    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert 'project_name = "my-cool-app"' in config_text


def test_init_with_external_archledger_dir_uses_directory_directly(
    tmp_path: Path,
) -> None:
    external_dir = tmp_path.parent / "architecture-state" / "demo"
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--archledger-dir",
            str(external_dir),
        ],
    )

    assert result.exit_code == 0
    assert external_dir.is_dir()
    assert (external_dir / "storage.yaml").is_file()
    assert not (external_dir / ".archledger").exists()


def test_cli_discovers_archledger_toml_from_subdirectory(tmp_path: Path) -> None:
    init_result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert init_result.exit_code == 0

    nested_dir = tmp_path / "src" / "pkg"
    nested_dir.mkdir(parents=True)
    result = runner.invoke(app, ["--root", str(nested_dir), "where"])

    assert result.exit_code == 0
    assert str(tmp_path / "archledger.toml") in result.stdout


def test_hidden_archledger_toml_is_supported(tmp_path: Path) -> None:
    hidden_config = tmp_path / ".archledger.toml"
    hidden_config.write_text(
        "\n".join(
            [
                "config_version = 1",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / ".archledger" / "sections").mkdir(parents=True)
    (tmp_path / ".archledger" / "records").mkdir(parents=True)
    (tmp_path / ".archledger" / "build").mkdir(parents=True)
    (tmp_path / ".archledger" / "storage.yaml").write_text(
        "\n".join(
            [
                "storage_version: 1",
                'created_with_archledger: "0.0.0"',
                'project_uuid: "12345678-1234-1234-1234-123456789abc"',
                'created_at: "2026-05-19T00:00:00Z"',
                "next_numbers:",
                "  stakeholder: 1",
                "  quality_goal: 1",
                "  constraint: 1",
                "  context_interface: 1",
                "  white_box: 1",
                "  black_box: 1",
                "  interface: 1",
                "  runtime: 1",
                "  infrastructure: 1",
                "  concept: 1",
                "  adr: 1",
                "  quality_scenario: 1",
                "  risk: 1",
                "  glossary: 1",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "where"])

    assert result.exit_code == 0
    assert str(hidden_config) in result.stdout


def test_invalid_archledger_toml_returns_json_error(tmp_path: Path) -> None:
    (tmp_path / "archledger.toml").write_text("this is not valid =", encoding="utf-8")

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "status"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "status"
    assert payload["error"]["type"] == "ConfigError"
