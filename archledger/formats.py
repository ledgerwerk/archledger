from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from archledger.errors import RenderError
from archledger.model import (
    OUTPUT_FORMAT_EXTENSIONS,
    VALID_OUTPUT_FORMATS,
    default_document_filename_for_output_format,
)
from archledger.storage.project_config import ProjectConfig


class OutputFormat(str, Enum):
    ASCIIDOC = "asciidoc"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    RST = "rst"
    TEXTILE = "textile"


ALL_OUTPUT_FORMATS = (
    OutputFormat.ASCIIDOC,
    OutputFormat.HTML,
    OutputFormat.PDF,
    OutputFormat.DOCX,
    OutputFormat.MARKDOWN,
    OutputFormat.RST,
    OutputFormat.TEXTILE,
)


@dataclass(frozen=True, slots=True)
class ResolvedOutput:
    format: OutputFormat
    output_path: Path


def parse_output_format(value: str) -> OutputFormat:
    normalized = value.strip().lower()
    try:
        return OutputFormat(normalized)
    except ValueError as exc:
        raise RenderError(
            "Unsupported output format: "
            f"{value}. Expected one of: {', '.join(sorted(VALID_OUTPUT_FORMATS))}."
        ) from exc


def parse_output_formats_csv(value: str) -> tuple[OutputFormat, ...]:
    formats: list[OutputFormat] = []
    seen: set[OutputFormat] = set()
    for item in value.split(","):
        output_format = parse_output_format(item)
        if output_format in seen:
            continue
        formats.append(output_format)
        seen.add(output_format)
    if not formats:
        raise RenderError("No output formats were provided.")
    return tuple(formats)


def infer_output_format_from_output_path(output: Path) -> OutputFormat:
    suffix = output.suffix.lower()
    for format_name, extension in OUTPUT_FORMAT_EXTENSIONS.items():
        if extension == suffix:
            return OutputFormat(format_name)
    raise RenderError(
        f"Cannot infer build format from output path: {output}. "
        "Pass --format explicitly or use a supported extension."
    )


def resolve_requested_formats(
    config: ProjectConfig,
    *,
    output: Path | None,
    format_name: str | None,
    formats_value: str | None,
    build_all: bool,
) -> tuple[OutputFormat, ...]:
    selected_options = sum(
        1 for value in (format_name, formats_value) if value not in (None, "")
    ) + int(build_all)
    if selected_options > 1:
        raise RenderError("Use only one of --format, --formats, or --all.")

    if build_all:
        requested_all_formats = tuple(
            output_format
            for output_format in ALL_OUTPUT_FORMATS
            if not _is_explicitly_disabled(config, output_format)
        )
        if requested_all_formats:
            return requested_all_formats
        raise RenderError("No output formats are enabled for build --all.")
    if formats_value:
        return parse_output_formats_csv(formats_value)
    if format_name:
        return (parse_output_format(format_name),)
    if output is not None:
        return (infer_output_format_from_output_path(output),)
    default_format = parse_output_format(config.build_default_format)
    default_requested_formats: list[OutputFormat] = [default_format]
    for output_format in ALL_OUTPUT_FORMATS:
        if output_format is default_format or not _is_explicitly_enabled(
            config, output_format
        ):
            continue
        default_requested_formats.append(output_format)
    return tuple(default_requested_formats)


def resolve_output_path(
    config: ProjectConfig,
    workspace_root: Path,
    build_dir: Path,
    requested_format: OutputFormat,
    output: Path | None,
) -> Path:
    if output is not None:
        if output.is_absolute():
            return output
        return workspace_root / output
    default_format = parse_output_format(config.build_default_format)
    if requested_format is default_format:
        return build_dir / Path(config.build_default_output)
    return build_dir / default_document_filename_for_output_format(
        requested_format.value
    )


def _is_explicitly_disabled(config: ProjectConfig, output_format: OutputFormat) -> bool:
    output_config = config.build_outputs.get(output_format.value, {})
    return output_config.get("enabled") is False


def _is_explicitly_enabled(config: ProjectConfig, output_format: OutputFormat) -> bool:
    output_config = config.build_outputs.get(output_format.value, {})
    return output_config.get("enabled") is True
