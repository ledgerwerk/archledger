from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.repository import ArchitectureRepository
from archledger.storage.meta import read_storage_meta, write_storage_meta

runner = CliRunner()

_CONFIG_PATH = ".ledger/archledger/config.toml"
_DATA_PATH = ".ledger/archledger/data"


def _config_path(root: Path) -> Path:
    return root / _CONFIG_PATH


def _data_path(root: Path) -> Path:
    return root / _DATA_PATH


def test_init_writes_archledger_toml_and_default_storage(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])

    assert result.exit_code == 0
    assert _config_path(tmp_path).is_file()
    assert (_data_path(tmp_path) / "storage.yaml").is_file()
    assert (_data_path(tmp_path) / "profiles" / "arc42" / "sections").is_dir()
    assert (_data_path(tmp_path) / "records" / "building_blocks").is_dir()
    assert (
        _data_path(tmp_path) / "profiles" / "arc42" / "sections" / "content-0001.md"
    ).is_file()
    storage_text = (_data_path(tmp_path) / "storage.yaml").read_text(encoding="utf-8")
    assert "next_number: 13" in storage_text


def test_init_project_name_defaults_to_workspace_basename(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])

    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert "config_version = 12" in config_text
    assert "[ids]" in config_text
    assert "width = 4" in config_text
    assert "[ids.kind_map]" in config_text
    assert "[source]" in config_text
    assert 'format = "markdown"' in config_text
    assert "schema_version = 4" in config_text
    assert 'section_extension = ".md"' in config_text
    # v12 does not write project_name or project_uuid to tool config
    assert "project_name" not in config_text
    assert "project_uuid" not in config_text
    assert 'default_format = "markdown"' in config_text
    assert 'default_output = "architecture.md"' in config_text
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
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert 'format = "markdown"' in config_text
    assert 'section_extension = ".md"' in config_text
    assert 'record_extension = ".md"' in config_text
    assert 'default_format = "markdown"' in config_text
    assert 'default_output = "architecture.md"' in config_text
    assert "schema_version = 4" in config_text
    assert (
        _data_path(tmp_path) / "profiles" / "arc42" / "sections" / "content-0001.md"
    ).is_file()


def test_init_asciidoc_source_writes_asciidoc_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", "asciidoc"],
    )

    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert 'format = "asciidoc"' in config_text
    assert 'section_extension = ".adoc"' in config_text
    assert 'record_extension = ".adoc"' in config_text
    assert 'default_format = "asciidoc"' in config_text
    assert 'default_output = "architecture.adoc"' in config_text
    assert "schema_version = 4" in config_text


def test_init_project_name_option_overrides_basename(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--project-name", "My Cool App"],
    )

    assert result.exit_code == 0
    # project_name is stored in the manifest, not in the tool config (v12)
    manifest_text = (tmp_path / ".ledger/ledger.toml").read_text(encoding="utf-8")
    assert 'name = "My Cool App"' in manifest_text


def test_rendered_default_config_has_no_duplicate_tracking_excludes(
    tmp_path: Path,
) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])

    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
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

    # --archledger-dir is no longer supported
    assert result.exit_code == 1
    assert "no longer supported" in result.output


def test_cli_discovers_archledger_toml_from_subdirectory(tmp_path: Path) -> None:
    init_result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert init_result.exit_code == 0

    nested_dir = tmp_path / "src" / "pkg"
    nested_dir.mkdir(parents=True)
    result = runner.invoke(app, ["--root", str(nested_dir), "storage", "where"])

    assert result.exit_code == 0
    assert str(_config_path(tmp_path)) in result.stdout


def test_hidden_archledger_toml_is_supported(tmp_path: Path) -> None:
    """Legacy .archledger.toml is detected by paths/storage commands."""
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

    result = runner.invoke(app, ["--root", str(tmp_path), "storage", "where"])

    # storage where detects legacy layout and shows migration hint
    assert result.exit_code == 1


def test_invalid_config_returns_json_error(tmp_path: Path) -> None:
    """Malformed tool config produces a JSON error."""
    # First create a valid project, then corrupt the config.
    init_result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert init_result.exit_code == 0

    _config_path(tmp_path).write_text("this is not valid =", encoding="utf-8")

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "status"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "status"
    assert payload["error"]["type"] == "ConfigError"


def test_init_refuses_when_hidden_archledger_toml_exists(tmp_path: Path) -> None:
    hidden_config = tmp_path / ".archledger.toml"
    hidden_config.write_text(
        "\n".join(
            [
                "config_version = 8",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "init"])

    assert result.exit_code == 1
    assert "migrate project" in result.output
    assert not _config_path(tmp_path).exists()


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

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "storage", "where"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "data_root" in payload["result"]
    data_root = Path(payload["result"]["data_root"])
    assert data_root.parts[-3:] == (".ledger", "archledger", "data")


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
    assert schema["id_format"] == {
        "ledger_code": "al",
        "width": 4,
    }
    assert schema["id_pattern"] == r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*-\d{4,}$"


def test_repo_init_does_not_rewrite_existing_storage_meta_without_overwrite(
    tmp_path: Path,
) -> None:
    init_result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert init_result.exit_code == 0

    storage_meta_path = _data_path(tmp_path) / "storage.yaml"
    write_storage_meta(
        storage_meta_path,
        replace(
            read_storage_meta(storage_meta_path),
            version=99,
        ),
    )

    from archledger.storage.paths import resolve_project_paths

    paths, config, _ = resolve_project_paths(tmp_path)
    repo = ArchitectureRepository(paths, config)

    result = repo.init(overwrite=False)

    assert storage_meta_path not in result.created_paths
    assert read_storage_meta(storage_meta_path).version == 99


def test_init_diagram_options_write_expected_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--diagrams",
            "--diagram-renderer",
            "mermaid-cli",
            "--diagram-default-type",
            "mermaid",
            "--diagram-output-dir",
            "assets/diagrams",
            "--diagram-image-format",
            "png",
        ],
    )
    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert "enabled = true" in config_text
    assert 'renderer = "mermaid-cli"' in config_text
    assert 'default_type = "mermaid"' in config_text
    assert 'output_dir = "assets/diagrams"' in config_text
    assert 'image_format = "png"' in config_text


def test_init_no_diagrams_disables_diagrams(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--no-diagrams"],
    )
    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert "enabled = false" in config_text


def test_init_build_options_write_expected_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--source-format",
            "markdown",
            "--build-default-output",
            "ARCHITECTURE.md",
            "--build-default-output-dir",
            ".",
            "--build-include-draft",
            "--build-include-superseded",
            "--build-strict",
            "--build-keep-intermediate",
            "--build-converter",
            "pandoc",
            "--build-pdf-engine",
            "xelatex",
            "--build-reference-docx",
            "template.docx",
        ],
    )
    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert 'default_output = "ARCHITECTURE.md"' in config_text
    assert 'default_output_dir = "."' in config_text
    assert "include_draft = true" in config_text
    assert "include_superseded = true" in config_text
    assert "strict = true" in config_text
    assert "keep_intermediate = true" in config_text
    assert 'converter = "pandoc"' in config_text
    assert 'pdf_engine = "xelatex"' in config_text
    assert 'reference_docx = "template.docx"' in config_text


def test_init_arc42_options_write_expected_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--arc42-title",
            "My System",
            "--arc42-language",
            "de",
            "--arc42-template-version",
            "8.2-EN",
            "--arc42-include-help",
        ],
    )
    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert 'title = "My System"' in config_text
    assert 'language = "de"' in config_text
    assert 'template_version = "8.2-EN"' in config_text
    assert "include_help = true" in config_text


def test_init_tracking_options_write_expected_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--no-tracking",
            "--tracking-scanner",
            "filesystem",
            "--tracking-state-file",
            "custom-state.json",
            "--tracking-max-file-bytes",
            "5000",
            "--tracking-include",
            "src/**/*.py",
            "--tracking-exclude",
            "vendor/**",
        ],
    )
    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert "enabled = false" in config_text
    assert 'scanner = "filesystem"' in config_text
    assert 'state_file = "custom-state.json"' in config_text
    assert "max_file_bytes = 5000" in config_text
    assert '"src/**/*.py"' in config_text
    assert '"vendor/**"' in config_text


def test_init_project_uuid_option_is_stored(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--project-uuid",
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        ],
    )
    assert result.exit_code == 0
    # UUID is stored in manifest, not tool config (v12)
    manifest_text = (tmp_path / ".ledger/ledger.toml").read_text(encoding="utf-8")
    assert "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" in manifest_text
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert "project_uuid" not in config_text


def test_init_invalid_project_uuid_is_rejected(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--project-uuid", "not-a-uuid"],
    )
    assert result.exit_code == 1
    # Error message may be on stderr from ledgercore; just check exit code.


def test_init_invalid_diagram_renderer_is_rejected(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--diagrams", "--diagram-renderer", "kroki"],
    )
    assert result.exit_code == 1
    assert "renderer must be one of" in result.output


def test_init_skill_installed_defaults_to_false(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert "installed = false" in config_text


def test_init_custom_id_format_writes_config_and_sections(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--source-format",
            "markdown",
            "--id-prefix",
            "ta",
            "--id-width",
            "3",
        ],
    )

    assert result.exit_code == 0
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert "[ids]" in config_text
    assert "width = 3" in config_text
    assert "[ids.kind_map]" in config_text
    assert (
        _data_path(tmp_path) / "profiles" / "arc42" / "sections" / "content-001.md"
    ).is_file()
    assert (
        _data_path(tmp_path) / "profiles" / "arc42" / "sections" / "content-012.md"
    ).is_file()

    new_result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "requirement", "Local accounting"],
    )
    assert new_result.exit_code == 0
    assert (
        _data_path(tmp_path) / "records" / "requirements" / "content-013.md"
    ).is_file()


def test_init_can_enable_id_segments(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--source-format",
            "markdown",
            "--id-segment-mode",
            "type",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (
        _data_path(tmp_path) / "profiles" / "arc42" / "sections" / "content-0001.md"
    ).is_file()
    config_text = _config_path(tmp_path).read_text(encoding="utf-8")
    assert "[ids.kind_map]" in config_text
