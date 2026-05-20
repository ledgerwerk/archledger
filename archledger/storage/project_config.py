from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from archledger.errors import ConfigError
from archledger.model import (
    VALID_OUTPUT_FORMATS,
    VALID_SOURCE_FORMATS,
    default_document_filename_for_output_format,
    default_extension_for_source_format,
    infer_output_format_from_path,
)
from archledger.storage.common import read_text

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib


_ALLOWED_TOP_LEVEL_KEYS = {
    "config_version",
    "archledger_dir",
    "project_uuid",
    "project_name",
    "source",
    "build",
    "arc42",
    "skill",
}
_ALLOWED_BUILD_KEYS = {
    "default_output",
    "default_format",
    "default_output_dir",
    "include_draft",
    "include_superseded",
    "strict",
    "keep_intermediate",
    "reference_docx",
    "outputs",
}
_ALLOWED_ARC42_KEYS = {"template_version", "language", "title", "include_help"}
_ALLOWED_SKILL_KEYS = {"installed", "path"}
_ALLOWED_SOURCE_KEYS = {
    "format",
    "front_matter",
    "section_extension",
    "record_extension",
}


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    config_version: int
    archledger_dir: str
    project_uuid: str
    project_name: str
    source_format: str = "markdown"
    front_matter: str = "yaml"
    section_extension: str = ".md"
    record_extension: str = ".md"
    build_default_output: str = "architecture.md"
    build_default_format: str = "markdown"
    build_output_dir: str = "build"
    build_include_draft: bool = False
    build_include_superseded: bool = False
    build_strict: bool = False
    build_keep_intermediate: bool = False
    build_reference_docx: str = ""
    build_outputs: dict[str, dict[str, object]] = field(default_factory=dict)
    arc42_template_version: str = "9.0-EN"
    arc42_language: str = "en"
    arc42_title: str = "Architecture Documentation"
    arc42_include_help: bool = False
    skill_installed: bool = False
    skill_path: str = "skills/archledger/SKILL.md"


def normalize_project_name(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", name.strip().lower()).strip("-")
    if not normalized:
        raise ConfigError("Project name must contain at least one letter or number.")
    return normalized


def render_default_config(
    workspace_root: Path,
    *,
    archledger_dir: str,
    project_name: str | None = None,
    project_uuid: str | None = None,
) -> str:
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
            "config_version = 3",
            f'archledger_dir = "{archledger_dir}"',
            "",
            "# Stable project identity. Commit this with your source tree.",
            f'project_uuid = "{normalized_uuid}"',
            f'project_name = "{normalized_project_name}"',
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
        ]
    )


def load_project_config(path: Path) -> ProjectConfig:
    try:
        raw_data = tomllib.loads(read_text(path))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Failed to parse {path.name}: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise ConfigError(f"{path.name} did not parse to a TOML table.")

    unknown_top_level = sorted(set(raw_data) - _ALLOWED_TOP_LEVEL_KEYS)
    if unknown_top_level:
        joined = ", ".join(unknown_top_level)
        raise ConfigError(f"Unknown config keys in {path.name}: {joined}")

    build_data = _validate_subtable(
        path,
        raw_data.get("build"),
        _ALLOWED_BUILD_KEYS,
        "build",
    )
    source_data = _validate_subtable(
        path,
        raw_data.get("source"),
        _ALLOWED_SOURCE_KEYS,
        "source",
    )
    arc42_data = _validate_subtable(
        path,
        raw_data.get("arc42"),
        _ALLOWED_ARC42_KEYS,
        "arc42",
    )
    skill_data = _validate_subtable(
        path,
        raw_data.get("skill"),
        _ALLOWED_SKILL_KEYS,
        "skill",
    )

    config_version = raw_data.get("config_version")
    if config_version not in {1, 2, 3}:
        raise ConfigError("config_version must be 1, 2, or 3.")

    archledger_dir = raw_data.get("archledger_dir")
    if not isinstance(archledger_dir, str) or not archledger_dir.strip():
        raise ConfigError("archledger_dir must be a non-empty string.")

    project_uuid = raw_data.get("project_uuid")
    if not isinstance(project_uuid, str):
        raise ConfigError("project_uuid must be a string.")

    project_name = raw_data.get("project_name")
    if not isinstance(project_name, str):
        raise ConfigError("project_name must be a string.")

    source_format, front_matter, section_extension, record_extension = (
        _parse_source_config(source_data, cast(int, config_version))
    )
    (
        default_output,
        build_default_format,
        output_dir,
        include_draft,
        include_superseded,
        strict,
        keep_intermediate,
        reference_docx,
        build_outputs,
    ) = _parse_build_config(build_data, cast(int, config_version), source_format)
    template_version, language, title, include_help = _parse_arc42_config(arc42_data)
    skill_installed, skill_path = _parse_skill_config(skill_data)

    return ProjectConfig(
        config_version=cast(int, config_version),
        archledger_dir=archledger_dir,
        project_uuid=_validate_uuid(project_uuid),
        project_name=normalize_project_name(project_name),
        source_format=source_format,
        front_matter=front_matter.strip().lower(),
        section_extension=section_extension,
        record_extension=record_extension,
        build_default_output=default_output,
        build_default_format=build_default_format,
        build_output_dir=output_dir.strip(),
        build_include_draft=include_draft,
        build_include_superseded=include_superseded,
        build_strict=strict,
        build_keep_intermediate=keep_intermediate,
        build_reference_docx=reference_docx,
        build_outputs=build_outputs,
        arc42_template_version=template_version,
        arc42_language=language,
        arc42_title=title,
        arc42_include_help=include_help,
        skill_installed=skill_installed,
        skill_path=skill_path,
    )


def _validate_subtable(
    path: Path,
    value: object,
    allowed_keys: set[str],
    table_name: str,
) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{table_name} in {path.name} must be a TOML table.")
    unknown_keys = sorted(set(value) - allowed_keys)
    if unknown_keys:
        joined = ", ".join(unknown_keys)
        raise ConfigError(f"Unknown keys in {table_name}: {joined}")
    return dict(value)


def _parse_source_config(
    source_data: dict[str, object],
    config_version: int,
) -> tuple[str, str, str, str]:
    source_format_default = "asciidoc" if config_version == 3 else "markdown"
    source_format_value = source_data.get("format", source_format_default)
    if not isinstance(source_format_value, str):
        raise ConfigError("source.format must be a string.")
    source_format = source_format_value.strip().lower()
    if source_format not in VALID_SOURCE_FORMATS:
        raise ConfigError(
            "source.format must be one of: "
            + ", ".join(sorted(VALID_SOURCE_FORMATS))
            + "."
        )

    front_matter_value = source_data.get("front_matter", "yaml")
    if (
        not isinstance(front_matter_value, str)
        or front_matter_value.strip().lower() != "yaml"
    ):
        raise ConfigError('source.front_matter must be the string "yaml".')

    default_extension = default_extension_for_source_format(source_format)
    section_extension = _normalize_extension(
        source_data.get("section_extension", default_extension),
        "source.section_extension",
    )
    record_extension = _normalize_extension(
        source_data.get("record_extension", default_extension),
        "source.record_extension",
    )
    return (
        source_format,
        front_matter_value.strip().lower(),
        section_extension,
        record_extension,
    )


def _parse_build_config(
    build_data: dict[str, object],
    config_version: int,
    source_format: str,
) -> tuple[
    str,
    str,
    str,
    bool,
    bool,
    bool,
    bool,
    str,
    dict[str, dict[str, object]],
]:
    default_output_value = build_data.get("default_output")
    if default_output_value is None:
        default_output = ""
    elif isinstance(default_output_value, str) and default_output_value.strip():
        default_output = default_output_value.strip()
    else:
        raise ConfigError("build.default_output must be a non-empty string.")

    default_format_value = build_data.get("default_format")
    if default_format_value is None:
        inferred_default_format = (
            infer_output_format_from_path(default_output) if default_output else None
        )
        build_default_format = source_format if config_version == 3 else "markdown"
        if inferred_default_format is not None:
            build_default_format = inferred_default_format
    elif isinstance(default_format_value, str):
        build_default_format = default_format_value.strip().lower()
        if build_default_format not in VALID_OUTPUT_FORMATS:
            raise ConfigError(
                "build.default_format must be one of: "
                + ", ".join(sorted(VALID_OUTPUT_FORMATS))
                + "."
            )
    else:
        raise ConfigError("build.default_format must be a string.")

    if not default_output:
        default_output = default_document_filename_for_output_format(
            build_default_format
        )

    output_dir = _require_non_empty_string(
        build_data.get("default_output_dir", "build"),
        "build.default_output_dir",
    )
    include_draft = _require_bool(
        build_data.get("include_draft", False),
        "build.include_draft",
    )
    include_superseded = _require_bool(
        build_data.get("include_superseded", False),
        "build.include_superseded",
    )
    strict = _require_bool(build_data.get("strict", False), "build.strict")
    keep_intermediate = _require_bool(
        build_data.get("keep_intermediate", False),
        "build.keep_intermediate",
    )
    reference_docx = build_data.get("reference_docx", "")
    if not isinstance(reference_docx, str):
        raise ConfigError("build.reference_docx must be a string.")

    outputs_value = build_data.get("outputs", {})
    if not isinstance(outputs_value, dict):
        raise ConfigError("build.outputs must be a TOML table.")
    build_outputs = _normalize_build_outputs(outputs_value)
    return (
        default_output,
        build_default_format,
        output_dir,
        include_draft,
        include_superseded,
        strict,
        keep_intermediate,
        reference_docx,
        build_outputs,
    )


def _parse_arc42_config(
    arc42_data: dict[str, object],
) -> tuple[str, str, str, bool]:
    template_version = _require_non_empty_string(
        arc42_data.get("template_version", "9.0-EN"),
        "arc42.template_version",
    )
    language = _require_non_empty_string(
        arc42_data.get("language", "en"),
        "arc42.language",
    )
    title = _require_non_empty_string(
        arc42_data.get("title", "Architecture Documentation"),
        "arc42.title",
    )
    include_help = _require_bool(
        arc42_data.get("include_help", False),
        "arc42.include_help",
    )
    return template_version, language, title, include_help


def _parse_skill_config(skill_data: dict[str, object]) -> tuple[bool, str]:
    skill_installed = _require_bool(
        skill_data.get("installed", False),
        "skill.installed",
    )
    skill_path = _require_non_empty_string(
        skill_data.get("path", "skills/archledger/SKILL.md"),
        "skill.path",
    )
    return skill_installed, skill_path


def _normalize_extension(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} must be a non-empty string.")
    normalized = value.strip().lower()
    if not normalized.startswith(".") or len(normalized) == 1:
        raise ConfigError(f"{field_name} must start with a file extension dot.")
    return normalized


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{field_name} must be a boolean.")
    return value


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _normalize_build_outputs(value: dict[str, object]) -> dict[str, dict[str, object]]:
    normalized: dict[str, dict[str, object]] = {}
    for output_name, raw_config in value.items():
        if not isinstance(raw_config, dict):
            raise ConfigError(f"build.outputs.{output_name} must be a TOML table.")
        normalized[output_name] = dict(raw_config)
    return normalized


def _validate_uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ConfigError("project_uuid must be a valid UUID.") from exc
