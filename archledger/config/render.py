from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

from archledger.config.model import (
    DEFAULT_ID_SEGMENT,
    DEFAULT_ID_SEGMENT_MAP,
    DEFAULT_TRACKING_EXCLUDE,
    DEFAULT_TRACKING_INCLUDE,
    VALID_BUILD_CONVERTERS,
    VALID_DIAGRAM_IMAGE_FORMATS,
    VALID_DIAGRAM_RENDERERS,
    VALID_DIAGRAM_TYPES,
    VALID_TRACKING_SCANNERS,
    ProjectConfig,
    normalize_project_name,
)
from archledger.errors import ConfigError
from archledger.ids import (
    DEFAULT_ID_PREFIX,
    DEFAULT_ID_SEGMENT_MODE,
    DEFAULT_ID_WIDTH,
    validate_id_prefix,
    validate_id_segment,
    validate_id_segment_mode,
    validate_id_width,
)
from archledger.model import (
    VALID_SOURCE_FORMATS,
    default_document_filename_for_output_format,
    default_extension_for_source_format,
    native_output_format_for_source_format,
)


def build_default_project_config(
    workspace_root: Path,
    *,
    archledger_dir: str,
    source_format: str = "asciidoc",
    id_prefix: str = DEFAULT_ID_PREFIX,
    id_width: int = DEFAULT_ID_WIDTH,
    id_segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
    id_default_segment: str = DEFAULT_ID_SEGMENT,
    id_segment_map: dict[str, str] | None = None,
    project_name: str | None = None,
    project_uuid: str | None = None,
    # Build options
    build_default_format: str | None = None,
    build_default_output: str | None = None,
    build_default_output_dir: str | None = None,
    build_include_draft: bool = False,
    build_include_superseded: bool = False,
    build_strict: bool = False,
    build_keep_intermediate: bool = False,
    build_converter: str = "auto",
    build_pdf_engine: str = "",
    build_reference_docx: str = "",
    # Diagram options
    diagram_enabled: bool = False,
    diagram_renderer: str = "pass-through",
    diagram_default_type: str = "text",
    diagram_output_dir: str = "diagrams",
    diagram_image_format: str = "svg",
    diagram_kroki_url: str = "",
    # arc42 options
    arc42_template_version: str = "9.0-EN",
    arc42_language: str = "en",
    arc42_title: str = "Architecture Documentation",
    arc42_include_help: bool = False,
    # Tracking options
    tracking_enabled: bool = True,
    tracking_scanner: str = "auto",
    tracking_state_file: str = "source-state.json",
    tracking_max_file_bytes: int = 1_000_000,
    tracking_include: tuple[str, ...] | None = None,
    tracking_exclude: tuple[str, ...] | None = None,
) -> ProjectConfig:
    normalized_source_format = source_format.strip().lower()
    if normalized_source_format not in VALID_SOURCE_FORMATS:
        raise ConfigError(
            "source_format must be one of: "
            + ", ".join(sorted(VALID_SOURCE_FORMATS))
            + "."
        )
    # Validate enum-like values before writing config
    _validate_enum(diagram_renderer, VALID_DIAGRAM_RENDERERS, "diagrams.renderer")
    _validate_enum(diagram_default_type, VALID_DIAGRAM_TYPES, "diagrams.default_type")
    _validate_enum(
        diagram_image_format, VALID_DIAGRAM_IMAGE_FORMATS, "diagrams.image_format"
    )
    _validate_enum(build_converter, VALID_BUILD_CONVERTERS, "build.converter")
    _validate_enum(tracking_scanner, VALID_TRACKING_SCANNERS, "tracking.scanner")
    validated_id_prefix = validate_id_prefix(id_prefix)
    validated_id_width = validate_id_width(id_width)
    validated_id_segment_mode = validate_id_segment_mode(id_segment_mode)
    validated_id_default_segment = validate_id_segment(id_default_segment)
    resolved_segment_map = dict(DEFAULT_ID_SEGMENT_MAP)
    if id_segment_map is not None:
        for key, value in id_segment_map.items():
            resolved_segment_map[key] = validate_id_segment(value)

    default_extension = default_extension_for_source_format(normalized_source_format)
    native_format = native_output_format_for_source_format(normalized_source_format)
    resolved_default_format = build_default_format or native_format
    resolved_default_output = (
        build_default_output
        or default_document_filename_for_output_format(resolved_default_format)
    )
    normalized_project_name = normalize_project_name(
        workspace_root.name if project_name is None else project_name
    )
    normalized_uuid = (
        str(uuid4()) if project_uuid is None else _validate_uuid(project_uuid)
    )
    return ProjectConfig(
        config_version=7,
        archledger_dir=archledger_dir,
        project_uuid=normalized_uuid,
        project_name=normalized_project_name,
        id_prefix=validated_id_prefix,
        id_width=validated_id_width,
        id_segment_mode=validated_id_segment_mode,
        id_default_segment=validated_id_default_segment,
        id_segment_map=resolved_segment_map,
        source_format=normalized_source_format,
        front_matter="yaml",
        section_extension=default_extension,
        record_extension=default_extension,
        build_default_output=resolved_default_output,
        build_default_format=resolved_default_format,
        build_output_dir=build_default_output_dir or "build",
        build_include_draft=build_include_draft,
        build_include_superseded=build_include_superseded,
        build_strict=build_strict,
        build_keep_intermediate=build_keep_intermediate,
        build_converter=build_converter,
        build_pdf_engine=build_pdf_engine,
        build_reference_docx=build_reference_docx,
        arc42_template_version=arc42_template_version,
        arc42_language=arc42_language,
        arc42_title=arc42_title,
        arc42_include_help=arc42_include_help,
        skill_installed=False,
        skill_path="skills/archledger/SKILL.md",
        tracking_enabled=tracking_enabled,
        tracking_state_file=tracking_state_file,
        tracking_scanner=tracking_scanner,
        tracking_include=tracking_include or DEFAULT_TRACKING_INCLUDE,
        tracking_exclude=tracking_exclude or DEFAULT_TRACKING_EXCLUDE,
        tracking_max_file_bytes=tracking_max_file_bytes,
        diagram_enabled=diagram_enabled,
        diagram_renderer=diagram_renderer,
        diagram_default_type=diagram_default_type,
        diagram_output_dir=diagram_output_dir,
        diagram_image_format=diagram_image_format,
        diagram_kroki_url=diagram_kroki_url,
    )


def render_default_config(
    workspace_root: Path,
    *,
    archledger_dir: str,
    source_format: str = "asciidoc",
    project_name: str | None = None,
    project_uuid: str | None = None,
) -> str:
    config = build_default_project_config(
        workspace_root,
        archledger_dir=archledger_dir,
        source_format=source_format,
        project_name=project_name,
        project_uuid=project_uuid,
    )
    return render_project_config(config)


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
        "[ids]",
        f"prefix = {_toml_string(config.id_prefix)}",
        f"width = {config.id_width}",
        f"segment_mode = {_toml_string(config.id_segment_mode)}",
        f"default_segment = {_toml_string(config.id_default_segment)}",
        "",
        "[ids.segment_map]",
    ]
    lines.extend(
        f"{segment_key} = {_toml_string(config.id_segment_map[segment_key])}"
        for segment_key in sorted(config.id_segment_map)
    )
    lines.extend(
        [
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
    )
    lines.extend(_render_build_output_tables(config.build_outputs))
    lines.extend(
        [
            "[diagrams]",
            f"enabled = {_toml_bool(config.diagram_enabled)}",
            f"renderer = {_toml_string(config.diagram_renderer)}",
            f"default_type = {_toml_string(config.diagram_default_type)}",
            f"output_dir = {_toml_string(config.diagram_output_dir)}",
            f"image_format = {_toml_string(config.diagram_image_format)}",
            f"kroki_url = {_toml_string(config.diagram_kroki_url)}",
            "",
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


def _validate_enum(value: str, allowed: frozenset[str], field_name: str) -> None:
    normalized = value.strip().lower()
    if normalized not in allowed:
        raise ConfigError(
            f"{field_name} must be one of: " + ", ".join(sorted(allowed)) + "."
        )
