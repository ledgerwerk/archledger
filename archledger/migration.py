from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from archledger.errors import RenderError
from archledger.storage.common import write_text
from archledger.storage.frontmatter import (
    iter_source_files,
    read_front_matter_document,
    write_front_matter_document,
)
from archledger.storage.paths import ProjectPaths
from archledger.storage.project_config import ProjectConfig


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

    source_paths = [
        *iter_source_files(paths.sections_dir, (config.section_extension,)),
        *iter_source_files(paths.records_dir, (config.record_extension,)),
    ]
    for source_path in source_paths:
        metadata, body = read_front_matter_document(source_path)
        converted_body, body_format, warning = _convert_body(body, pandoc)
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
        write_text(paths.config_path, _render_migrated_config(config))

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
) -> tuple[str, str, str | None]:
    if pandoc is None:
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
                "Cannot convert Markdown source body with pandoc.\n"
                f"{details}"
            )
        raise RenderError("Cannot convert Markdown source body with pandoc.")
    return (result.stdout, "asciidoc", None)


def _render_migrated_config(config: ProjectConfig) -> str:
    return "\n".join(
        [
            "# Project-local archledger configuration.",
            "# This file lives in the source project root.",
            "config_version = 3",
            f'archledger_dir = "{config.archledger_dir}"',
            "",
            "# Stable project identity. Commit this with your source tree.",
            f'project_uuid = "{config.project_uuid}"',
            f'project_name = "{config.project_name}"',
            "",
            "[source]",
            'format = "asciidoc"',
            'front_matter = "yaml"',
            'section_extension = ".adoc"',
            'record_extension = ".adoc"',
            "",
            "[build]",
            'default_format = "asciidoc"',
            f"include_draft = {'true' if config.build_include_draft else 'false'}",
            (
                "include_superseded = "
                f"{'true' if config.build_include_superseded else 'false'}"
            ),
            f"strict = {'true' if config.build_strict else 'false'}",
            "",
            "[arc42]",
            f'template_version = "{config.arc42_template_version}"',
            f'language = "{config.arc42_language}"',
            f'title = "{config.arc42_title}"',
            f"include_help = {'true' if config.arc42_include_help else 'false'}",
            "",
            "[skill]",
            f"installed = {'true' if config.skill_installed else 'false'}",
            f'path = "{config.skill_path}"',
            "",
        ]
    )
