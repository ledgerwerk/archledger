from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

from archledger.errors import RenderError
from archledger.model import (
    default_document_filename_for_output_format,
    native_output_format_for_source_format,
)
from archledger.storage.common import write_text_atomic
from archledger.storage.frontmatter import (
    iter_source_files,
    read_front_matter_document,
    write_front_matter_document,
)
from archledger.storage.paths import ProjectPaths
from archledger.storage.project_config import ProjectConfig, render_project_config


@dataclass(frozen=True, slots=True)
class ConvertedSource:
    source_path: Path
    output_path: Path
    body_format: str


@dataclass(frozen=True, slots=True)
class MigrationResult:
    target_format: str
    write: bool
    replace: bool
    config_path: Path
    converted: tuple[ConvertedSource, ...]
    warnings: tuple[str, ...]


def convert_sources(
    paths: ProjectPaths,
    config: ProjectConfig,
    *,
    target_format: str,
    write: bool,
    replace: bool,
    allow_mixed_body_format: bool = False,
) -> MigrationResult:
    normalized_target = target_format.strip().lower()
    if normalized_target != "asciidoc":
        raise RenderError(f"Unsupported conversion target: {target_format}")
    if replace and not write:
        raise RenderError("Use --write when combining convert-sources with --replace.")
    if config.source_format != "markdown":
        raise RenderError(
            "convert-sources currently supports Markdown source projects only."
        )

    warnings: list[str] = []
    converted: list[ConvertedSource] = []
    pandoc = shutil.which("pandoc")
    mixed_body_format_allowed = allow_mixed_body_format or not write
    if write and pandoc is None and not allow_mixed_body_format:
        raise RenderError(
            "Cannot write an AsciiDoc source migration without pandoc.\n"
            "Install pandoc or re-run with --allow-mixed-body-format."
        )

    source_paths = [
        *iter_source_files(paths.sections_dir, (config.section_extension,)),
        *iter_source_files(paths.records_dir, (config.record_extension,)),
    ]
    for source_path in source_paths:
        metadata, body = read_front_matter_document(source_path)
        converted_body, body_format, warning = _convert_body(
            body,
            pandoc,
            allow_mixed_body_format=mixed_body_format_allowed,
        )
        if warning is not None:
            warnings.append(f"{source_path}: {warning}")
        output_path = source_path.with_suffix(".adoc")
        if output_path.exists() and output_path != source_path:
            raise RenderError(
                f"Refusing to overwrite existing migrated source: {output_path}"
            )
        converted.append(
            ConvertedSource(
                source_path=source_path,
                output_path=output_path,
                body_format=body_format,
            )
        )
        if not write:
            continue

        migrated_metadata = dict(metadata)
        migrated_metadata["schema_version"] = 2
        migrated_metadata["body_format"] = body_format
        write_front_matter_document(output_path, migrated_metadata, converted_body)
        if replace:
            source_path.unlink()

    if write:
        write_text_atomic(
            paths.config_path,
            render_project_config(_migrated_config(config)),
        )

    return MigrationResult(
        target_format=normalized_target,
        write=write,
        replace=replace,
        config_path=paths.config_path,
        converted=tuple(converted),
        warnings=tuple(warnings),
    )


def _convert_body(
    body: str,
    pandoc: str | None,
    *,
    allow_mixed_body_format: bool,
) -> tuple[str, str, str | None]:
    if pandoc is None:
        if not allow_mixed_body_format:
            raise RenderError(
                "Cannot write an AsciiDoc source migration without pandoc.\n"
                "Install pandoc or re-run with --allow-mixed-body-format."
            )
        return (
            body,
            "markdown",
            "pandoc not found; kept Markdown body and marked body_format=markdown.",
        )

    result = subprocess.run(
        [pandoc, "-f", "markdown", "-t", "asciidoc"],
        input=body,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        if details:
            raise RenderError(
                f"Cannot convert Markdown source body with pandoc.\n{details}"
            )
        raise RenderError("Cannot convert Markdown source body with pandoc.")
    return (result.stdout, "asciidoc", None)


def _migrated_config(config: ProjectConfig) -> ProjectConfig:
    previous_native_format = native_output_format_for_source_format(
        config.source_format
    )
    default_format = config.build_default_format
    default_output = config.build_default_output
    if default_format == previous_native_format:
        default_format = "asciidoc"
        previous_native_output = default_document_filename_for_output_format(
            previous_native_format
        )
        if default_output == previous_native_output:
            default_output = default_document_filename_for_output_format("asciidoc")
    return replace(
        config,
        config_version=max(config.config_version, 5),
        source_format="asciidoc",
        section_extension=".adoc",
        record_extension=".adoc",
        build_default_output=default_output,
        build_default_format=default_format,
    )
