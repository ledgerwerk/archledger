from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.repository import ArchitectureRepository
from archledger.storage.meta import read_storage_meta, write_storage_meta
from archledger.storage.paths import resolve_project_paths
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
    assert "config_version = 5" in config_text
    assert "[source]" in config_text
    assert 'format = "asciidoc"' in config_text
    assert "schema_version = 2" in config_text
    assert 'section_extension = ".adoc"' in config_text
    assert f'project_name = "{normalize_project_name(tmp_path.name)}"' in config_text
    assert 'default_format = "asciidoc"' in config_text
    assert 'default_output = "architecture.adoc"' in config_text
    assert 'default_output_dir = "build"' in config_text
    assert "include_superseded = false" in config_text
    assert 'converter = "auto"' in config_text
    assert "[skill]" in config_text
    assert "[tracking]" in config_text
    assert 'state_file = "source-state.json"' in config_text
    assert 'scanner = "auto"' in config_text


def test_init_markdown_source_writes_markdown_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", "markdown"],
    )

    assert result.exit_code == 0
    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert 'format = "markdown"' in config_text
    assert 'section_extension = ".md"' in config_text
    assert 'record_extension = ".md"' in config_text
    assert 'default_format = "markdown"' in config_text
    assert 'default_output = "architecture.md"' in config_text
    assert "schema_version = 2" in config_text
    assert (
        tmp_path / ".archledger" / "sections" / "01_introduction_and_goals.md"
    ).is_file()


def test_init_asciidoc_source_writes_asciidoc_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", "asciidoc"],
    )

    assert result.exit_code == 0
    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert 'format = "asciidoc"' in config_text
    assert 'section_extension = ".adoc"' in config_text
    assert 'record_extension = ".adoc"' in config_text
    assert 'default_format = "asciidoc"' in config_text
    assert 'default_output = "architecture.adoc"' in config_text
    assert "schema_version = 2" in config_text


def test_init_project_name_option_overrides_basename(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--project-name", "My Cool App"],
    )

    assert result.exit_code == 0
    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert 'project_name = "my-cool-app"' in config_text


def test_rendered_default_config_has_no_duplicate_tracking_excludes(
    tmp_path: Path,
) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])

    assert result.exit_code == 0
    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert config_text.count('"**/__pycache__/**"') == 1


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
    result = runner.invoke(app, ["--root", str(nested_dir), "paths"])

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

    result = runner.invoke(app, ["--root", str(tmp_path), "paths"])

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


def test_invalid_source_format_is_rejected(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", "rst"],
    )

    assert result.exit_code == 1
    assert "source_format must be one of" in result.output


def test_paths_json_includes_source_state_path(tmp_path: Path) -> None:
    init_result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "paths"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "paths"
    assert payload["result"]["source_state_path"].endswith(
        ".archledger/source-state.json"
    )


def test_schema_json_lists_record_types_statuses_sections_and_formats(
    tmp_path: Path,
) -> None:
    init_result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "schema"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    schema = payload["result"]
    assert payload["command"] == "schema"
    assert schema["schema"] == "archledger.schema.v1"
    assert schema["record_types"]
    assert schema["statuses"]
    assert schema["sections"]
    assert schema["source_formats"]
    assert schema["output_formats"]


def test_repo_init_does_not_rewrite_existing_storage_meta_without_overwrite(
    tmp_path: Path,
) -> None:
    init_result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert init_result.exit_code == 0

    storage_meta_path = tmp_path / ".archledger" / "storage.yaml"
    write_storage_meta(
        storage_meta_path,
        replace(
            read_storage_meta(storage_meta_path),
            created_at="1999-12-31T23:59:59Z",
        ),
    )

    paths, config, _ = resolve_project_paths(tmp_path)
    repo = ArchitectureRepository(paths, config)

    result = repo.init(overwrite=False)

    assert storage_meta_path not in result.created_paths
    assert read_storage_meta(storage_meta_path).created_at == "1999-12-31T23:59:59Z"
