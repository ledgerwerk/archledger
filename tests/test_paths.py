from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

from archledger.errors import ConfigError
from archledger.storage.paths import resolve_project_paths
from archledger.storage.project_config import ProjectConfig


def test_relative_archledger_dir_is_relative_to_config_path(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 1",
                'archledger_dir = "../shared-state/demo"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    paths, _, warnings = resolve_project_paths(workspace_root)

    assert warnings == []
    assert paths.archledger_dir == (workspace_root / "../shared-state/demo").resolve()


def test_v2_config_supports_new_build_arc42_and_skill_keys(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace-v2"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 2",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[build]",
                'default_output = "docs/architecture.md"',
                "include_draft = false",
                "include_superseded = true",
                "strict = false",
                "",
                "[arc42]",
                'template_version = "9.0-EN"',
                'language = "en"',
                'title = "Architecture Documentation"',
                "include_help = true",
                "",
                "[skill]",
                "installed = true",
                'path = "skills/archledger/SKILL.md"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    paths, config, warnings = resolve_project_paths(workspace_root)

    assert warnings == []
    assert config.config_version == 2
    assert config.build_include_superseded is True
    assert config.arc42_include_help is True
    assert config.skill_installed is True
    assert config.skill_path == "skills/archledger/SKILL.md"


def test_v3_config_supports_source_format_extensions(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace-v3"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 3",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[source]",
                'format = "asciidoc"',
                'front_matter = "yaml"',
                'section_extension = ".adoc"',
                'record_extension = ".adoc"',
                "",
                "[build]",
                'default_format = "asciidoc"',
                "include_draft = false",
                "include_superseded = false",
                "strict = false",
                "",
            ]
        ),
        encoding="utf-8",
    )

    paths, config, warnings = resolve_project_paths(workspace_root)

    assert warnings == []
    assert config.config_version == 3
    assert config.source_format == "asciidoc"
    assert config.front_matter == "yaml"
    assert config.section_extension == ".adoc"
    assert config.record_extension == ".adoc"
    assert config.build_default_format == "asciidoc"
    assert config.build_default_output == "architecture.adoc"


def test_v4_config_supports_source_schema_version(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace-v4"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 4",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[source]",
                'format = "markdown"',
                'front_matter = "yaml"',
                'section_extension = ".md"',
                'record_extension = ".md"',
                "schema_version = 2",
                "",
                "[build]",
                'default_format = "markdown"',
                'default_output_dir = "build"',
                "include_draft = false",
                "include_superseded = false",
                "strict = false",
                "keep_intermediate = false",
                'converter = "auto"',
                'pdf_engine = "tectonic"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    paths, config, warnings = resolve_project_paths(workspace_root)

    assert warnings == []
    assert config.config_version == 4
    assert config.source_format == "markdown"
    assert config.source_schema_version == 2
    assert config.build_default_format == "markdown"
    assert config.build_default_output == "architecture.md"
    assert config.build_output_dir == "build"
    assert config.build_converter == "auto"
    assert config.build_pdf_engine == "tectonic"
    assert config.tracking_enabled is True
    assert config.tracking_state_file == "source-state.json"
    assert config.tracking_scanner == "auto"
    assert (
        paths.source_state_path == workspace_root / ".archledger" / "source-state.json"
    )


def test_v5_config_supports_tracking_settings(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace-v5"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 5",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[source]",
                'format = "markdown"',
                'front_matter = "yaml"',
                'section_extension = ".md"',
                'record_extension = ".md"',
                "schema_version = 2",
                "",
                "[tracking]",
                "enabled = true",
                'state_file = "tracking/source-state.json"',
                'scanner = "filesystem"',
                'include = ["**/*.py", "**/*.md"]',
                'exclude = [".git/**", ".archledger/**"]',
                "max_file_bytes = 2048",
                'hash_algorithm = "sha256"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    paths, config, warnings = resolve_project_paths(workspace_root)

    assert warnings == []
    assert config.config_version == 5
    assert config.tracking_enabled is True
    assert config.tracking_state_file == "tracking/source-state.json"
    assert config.tracking_scanner == "filesystem"
    assert config.tracking_include == ("**/*.py", "**/*.md")
    assert config.tracking_exclude == (".git/**", ".archledger/**")
    assert config.tracking_max_file_bytes == 2048
    assert config.tracking_hash_algorithm == "sha256"
    assert config.source.format == "markdown"
    assert config.build.default_output_dir == "build"
    assert config.build.outputs == {}
    assert config.arc42.title == "Architecture Documentation"
    assert config.skill.path == "skills/archledger/SKILL.md"
    assert config.tracking.state_file == "tracking/source-state.json"
    assert paths.source_state_path == (
        workspace_root / ".archledger" / "tracking" / "source-state.json"
    )


def test_project_config_fields_are_accounted_for() -> None:
    # Behavior-linked fields have dedicated tests across build/path/migration/tracking
    # coverage; metadata-only fields are kept explicit here so new parsed fields
    # cannot be added silently without test updates.
    behavior_or_metadata_fields = {
        "config_version",
        "archledger_dir",
        "project_uuid",
        "project_name",
        "source_format",
        "source_schema_version",
        "front_matter",
        "section_extension",
        "record_extension",
        "build_default_output",
        "build_default_format",
        "build_output_dir",
        "build_include_draft",
        "build_include_superseded",
        "build_strict",
        "build_keep_intermediate",
        "build_converter",
        "build_pdf_engine",
        "build_reference_docx",
        "build_outputs",
        "arc42_template_version",
        "arc42_language",
        "arc42_title",
        "arc42_include_help",
        "skill_installed",
        "skill_path",
        "tracking_enabled",
        "tracking_state_file",
        "tracking_scanner",
        "tracking_include",
        "tracking_exclude",
        "tracking_max_file_bytes",
        "tracking_hash_algorithm",
    }
    assert {item.name for item in fields(ProjectConfig)} == behavior_or_metadata_fields


def test_tracking_state_file_must_stay_inside_archledger_dir(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace-escape"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 5",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[source]",
                'format = "markdown"',
                "",
                "[tracking]",
                'state_file = "../source-state.json"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        resolve_project_paths(workspace_root)
    assert str(excinfo.value) == "tracking.state_file must stay inside archledger_dir."


def test_build_output_dir_must_stay_inside_archledger_dir(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace-build-output-dir-escape"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 5",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[source]",
                'format = "markdown"',
                "",
                "[build]",
                'default_output_dir = "../build"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        resolve_project_paths(workspace_root)
    assert (
        str(excinfo.value)
        == "build.default_output_dir must stay inside archledger_dir."
    )


def test_build_default_output_must_stay_inside_build_output_dir(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace-build-output-escape"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 5",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[source]",
                'format = "markdown"',
                "",
                "[build]",
                'default_output = "../architecture.md"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        resolve_project_paths(workspace_root)
    assert (
        str(excinfo.value)
        == "build.default_output must stay inside build.default_output_dir."
    )


def test_build_default_output_extension_must_match_default_format(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace-build-output-extension"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 5",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[source]",
                'format = "markdown"',
                "",
                "[build]",
                'default_format = "markdown"',
                'default_output = "architecture.html"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        resolve_project_paths(workspace_root)
    assert (
        str(excinfo.value)
        == "build.default_output extension must match build.default_format."
    )


def test_build_outputs_rejects_unknown_output_format(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace-invalid-output-format"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 5",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[source]",
                'format = "markdown"',
                "",
                "[build.outputs.epub]",
                'tool = "pandoc"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        resolve_project_paths(workspace_root)
    assert str(excinfo.value) == "build.outputs.epub is not a supported output format."


@pytest.mark.parametrize(
    ("config_lines", "message"),
    [
        (
            ['tool = "wrong"'],
            "build.outputs.html.tool must be one of: asciidoctor, auto, pandoc.",
        ),
        (
            ['unknown = "value"'],
            "Unknown keys in build.outputs.html: unknown",
        ),
        (
            ["pdf_engine = 123"],
            "build.outputs.html.pdf_engine must be a string.",
        ),
    ],
)
def test_build_outputs_validate_per_output_settings(
    tmp_path: Path,
    config_lines: list[str],
    message: str,
) -> None:
    workspace_root = tmp_path / "workspace-invalid-output-settings"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 5",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[source]",
                'format = "asciidoc"',
                "",
                "[build.outputs.html]",
                *config_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        resolve_project_paths(workspace_root)
    assert str(excinfo.value) == message


def test_config_version_bool_is_rejected(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace-invalid-config-version"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = true",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        resolve_project_paths(workspace_root)
    assert str(excinfo.value) == "config_version must be 1, 2, 3, 4, or 5."


@pytest.mark.parametrize(
    ("config_lines", "message"),
    [
        (
            [
                "[source]",
                'format = "markdown"',
                "schema_version = true",
            ],
            "source.schema_version must be an integer.",
        ),
        (
            [
                "[source]",
                'format = "markdown"',
                "",
                "[tracking]",
                "max_file_bytes = true",
            ],
            "tracking.max_file_bytes must be a positive integer.",
        ),
    ],
)
def test_integer_like_config_fields_reject_booleans(
    tmp_path: Path,
    config_lines: list[str],
    message: str,
) -> None:
    workspace_root = tmp_path / "workspace-invalid-integer-like-bool"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 5",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                *config_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        resolve_project_paths(workspace_root)
    assert str(excinfo.value) == message
