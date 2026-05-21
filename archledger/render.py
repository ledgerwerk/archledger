from __future__ import annotations

from pathlib import Path

from archledger.assembly import assemble_document
from archledger.converters import BuildResult, convert_assembled_document
from archledger.formats import (
    parse_output_format,
    resolve_output_path,
    resolve_requested_formats,
)
from archledger.model import native_output_format_for_source_format
from archledger.repository import ArchitectureRepository


def build_document(
    repo: ArchitectureRepository,
    *,
    output: Path | None = None,
    format: str | None = None,
    formats: str | None = None,
    all_formats: bool = False,
    include_draft: bool = False,
    include_superseded: bool = False,
    strict: bool = False,
) -> BuildResult:
    requested_formats = resolve_requested_formats(
        repo.config,
        output=output,
        format_name=format,
        formats_value=formats,
        build_all=all_formats,
    )
    native_format = parse_output_format(
        native_output_format_for_source_format(repo.config.source_format)
    )
    assembly_output: Path | None = None
    if (
        output is not None
        and len(requested_formats) == 1
        and requested_formats[0] is native_format
    ):
        assembly_output = resolve_output_path(
            repo.config,
            repo.paths.workspace_root,
            repo.paths.build_dir,
            native_format,
            output,
        )
    elif native_format in requested_formats:
        assembly_output = resolve_output_path(
            repo.config,
            repo.paths.workspace_root,
            repo.paths.build_dir,
            native_format,
            None,
        )
    assembly = assemble_document(
        repo,
        output=assembly_output,
        source_format=repo.config.source_format,
        include_draft=include_draft,
        include_superseded=include_superseded,
        strict=strict,
        write=True,
    )
    return convert_assembled_document(
        repo.config,
        repo.paths.workspace_root,
        repo.paths.build_dir,
        assembly,
        requested_formats,
        output=output,
    )
