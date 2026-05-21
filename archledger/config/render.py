from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

from archledger.config.model import ProjectConfig, normalize_project_name
from archledger.errors import ConfigError
from archledger.model import (
    CURRENT_SOURCE_SCHEMA_VERSION,
    VALID_SOURCE_FORMATS,
    default_document_filename_for_output_format,
    default_extension_for_source_format,
    native_output_format_for_source_format,
)


def render_default_config(
    workspace_root: Path,
    *,
    archledger_dir: str,
    source_format: str = "asciidoc",
    project_name: str | None = None,
    project_uuid: str | None = None,
) -> str:
    normalized_source_format = source_format.strip().lower()
    if normalized_source_format not in VALID_SOURCE_FORMATS:
        raise ConfigError(
            "source_format must be one of: "
            + ", ".join(sorted(VALID_SOURCE_FORMATS))
            + "."
        )
    default_extension = default_extension_for_source_format(normalized_source_format)
    default_format = native_output_format_for_source_format(normalized_source_format)
    default_output = default_document_filename_for_output_format(default_format)
    normalized_project_name = normalize_project_name(
        workspace_root.name if project_name is None else project_name
    )
    normalized_uuid = (
        str(uuid4()) if project_uuid is None else _validate_uuid(project_uuid)
    )
    return "\n".join(
        [
            "# Project-local archledger configuration.",
            "# This file lives in the source project root.",
            "config_version = 5",
            f'archledger_dir = "{archledger_dir}"',
            "",
            "# Stable project identity. Commit this with your source tree.",
            f'project_uuid = "{normalized_uuid}"',
            f'project_name = "{normalized_project_name}"',
            "",
            "[source]",
            f'format = "{normalized_source_format}"',
            'front_matter = "yaml"',
            f'section_extension = "{default_extension}"',
            f'record_extension = "{default_extension}"',
            f"schema_version = {CURRENT_SOURCE_SCHEMA_VERSION}",
            "",
            "[build]",
            f'default_format = "{default_format}"',
            f'default_output = "{default_output}"',
            "# [build].default_output_dir is relative to the directory containing",
            "# archledger.toml or .archledger.toml.",
            'default_output_dir = "build"',
            "include_draft = false",
            "include_superseded = false",
            "strict = false",
            "keep_intermediate = false",
            'converter = "auto"',
            "",
            "[arc42]",
            'template_version = "9.0-EN"',
            'language = "en"',
            'title = "Architecture Documentation"',
            "include_help = false",
            "",
            "[skill]",
            "installed = true",
            'path = "skills/archledger/SKILL.md"',
            "",
            "[tracking]",
            "enabled = true",
            "# source-state.json stores SHA-256 content hashes only for files.",
            "# It does not persist mtimes or file sizes. Directory hashes are",
            "# derived from file hashes after scanning.",
            'state_file = "source-state.json"',
            'scanner = "auto"',
            "include = [",
            '  "**/*.py",',
            '  "**/*.toml",',
            '  "**/*.md",',
            '  "**/*.adoc",',
            '  "**/*.rst",',
            '  "**/*.j2",',
            '  "**/*.yaml",',
            '  "**/*.yml",',
            '  "**/*.json",',
            "]",
            "exclude = [",
            '  ".git/**",',
            '  ".venv/**",',
            '  "**/__pycache__/**",',
            '  ".mypy_cache/**",',
            '  ".pytest_cache/**",',
            '  ".ruff_cache/**",',
            '  "dist/**",',
            '  "build/**",',
            "]",
            "max_file_bytes = 1000000",
            'hash_algorithm = "sha256"',
            "",
        ]
    )


def render_project_config(config: ProjectConfig) -> str:
    lines = [
        "# Project-local archledger configuration.",
        "# This file lives in the source project root.",
        f"config_version = {config.config_version}",
        f"archledger_dir = {_toml_string(config.archledger_dir)}",
        "",
        "# Stable project identity. Commit this with your source tree.",
        f"project_uuid = {_toml_string(config.project_uuid)}",
        f"project_name = {_toml_string(config.project_name)}",
        "",
        "[source]",
        f"format = {_toml_string(config.source_format)}",
        f"front_matter = {_toml_string(config.front_matter)}",
        f"section_extension = {_toml_string(config.section_extension)}",
        f"record_extension = {_toml_string(config.record_extension)}",
        f"schema_version = {config.source_schema_version}",
        "",
        "[build]",
        f"default_output = {_toml_string(config.build_default_output)}",
        f"default_format = {_toml_string(config.build_default_format)}",
        "# [build].default_output_dir is relative to the directory containing",
        "# archledger.toml or .archledger.toml.",
        f"default_output_dir = {_toml_string(config.build_output_dir)}",
        f"include_draft = {_toml_bool(config.build_include_draft)}",
        f"include_superseded = {_toml_bool(config.build_include_superseded)}",
        f"strict = {_toml_bool(config.build_strict)}",
        f"keep_intermediate = {_toml_bool(config.build_keep_intermediate)}",
        f"converter = {_toml_string(config.build_converter)}",
        f"pdf_engine = {_toml_string(config.build_pdf_engine)}",
        f"reference_docx = {_toml_string(config.build_reference_docx)}",
        "",
    ]
    lines.extend(_render_build_output_tables(config.build_outputs))
    lines.extend(
        [
            "[arc42]",
            f"template_version = {_toml_string(config.arc42_template_version)}",
            f"language = {_toml_string(config.arc42_language)}",
            f"title = {_toml_string(config.arc42_title)}",
            f"include_help = {_toml_bool(config.arc42_include_help)}",
            "",
            "[skill]",
            f"installed = {_toml_bool(config.skill_installed)}",
            f"path = {_toml_string(config.skill_path)}",
            "",
            "[tracking]",
            f"enabled = {_toml_bool(config.tracking_enabled)}",
            "# source-state.json stores SHA-256 content hashes only for files.",
            "# It does not persist mtimes or file sizes. Directory hashes are",
            "# derived from file hashes after scanning.",
            f"state_file = {_toml_string(config.tracking_state_file)}",
            f"scanner = {_toml_string(config.tracking_scanner)}",
            "include = [",
        ]
    )
    lines.extend(f"  {_toml_string(item)}," for item in config.tracking_include)
    lines.extend(["]", "exclude = ["])
    lines.extend(f"  {_toml_string(item)}," for item in config.tracking_exclude)
    lines.extend(
        [
            "]",
            f"max_file_bytes = {config.tracking_max_file_bytes}",
            f"hash_algorithm = {_toml_string(config.tracking_hash_algorithm)}",
            "",
        ]
    )
    return "\n".join(lines)


def _render_build_output_tables(
    build_outputs: dict[str, dict[str, object]],
) -> list[str]:
    lines: list[str] = []
    for output_name in sorted(build_outputs):
        output_config = build_outputs[output_name]
        lines.append(f"[build.outputs.{output_name}]")
        if "enabled" in output_config:
            lines.append(f"enabled = {_toml_bool(bool(output_config['enabled']))}")
        if "tool" in output_config:
            lines.append(f"tool = {_toml_string(str(output_config['tool']))}")
        if "pdf_engine" in output_config:
            lines.append(
                f"pdf_engine = {_toml_string(str(output_config['pdf_engine']))}"
            )
        if "reference_docx" in output_config:
            lines.append(
                "reference_docx = " + _toml_string(str(output_config["reference_docx"]))
            )
        lines.append("")
    return lines


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _validate_uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ConfigError("project_uuid must be a valid UUID.") from exc
