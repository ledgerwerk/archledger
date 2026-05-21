from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from archledger.assembly import AssemblyResult
from archledger.conversion_plan import (
    ConversionPlan,
    docbook_output_path,
    install_hint,
    plan_conversion,
    require_tool,
)
from archledger.errors import RenderError
from archledger.formats import OutputFormat, resolve_output_path
from archledger.storage.common import write_text
from archledger.storage.project_config import ProjectConfig


@dataclass(frozen=True, slots=True)
class ConversionResult:
    format: str
    output_path: Path
    command: tuple[str, ...] | None
    skipped: bool = False


@dataclass(frozen=True, slots=True)
class BuildResult:
    assembled_path: Path
    outputs: tuple[ConversionResult, ...]


def convert_assembled_document(
    config: ProjectConfig,
    workspace_root: Path,
    build_dir: Path,
    assembly: AssemblyResult,
    requested_formats: tuple[OutputFormat, ...],
    *,
    output: Path | None = None,
) -> BuildResult:
    if output is not None and len(requested_formats) != 1:
        raise RenderError("Use --output only when building a single format.")

    outputs: list[ConversionResult] = []
    docbook_path: Path | None = None
    try:
        for requested_format in requested_formats:
            output_path = resolve_output_path(
                config,
                workspace_root,
                build_dir,
                requested_format,
                output,
            )
            plan = plan_conversion(
                config,
                assembly,
                requested_format,
                output_path,
                tool_resolver=shutil.which,
            )
            if plan.native_copy:
                outputs.append(_build_native_output(assembly, plan))
                continue
            command = list(plan.command or [])
            if plan.requires_docbook:
                if docbook_path is None:
                    docbook_path = _build_docbook_intermediate(
                        assembly, requested_format
                    )
                command[-1] = str(docbook_path)
            _run_command(command, requested_format)
            outputs.append(
                ConversionResult(
                    format=requested_format.value,
                    output_path=plan.output_path,
                    command=tuple(command),
                )
            )
    finally:
        if docbook_path is not None and not config.build_keep_intermediate:
            docbook_path.unlink(missing_ok=True)
    return BuildResult(assembled_path=assembly.output_path, outputs=tuple(outputs))


def _build_native_output(
    assembly: AssemblyResult,
    plan: ConversionPlan,
) -> ConversionResult:
    if plan.output_path != assembly.output_path:
        write_text(plan.output_path, assembly.rendered_text)
    return ConversionResult(
        format=plan.requested_format.value,
        output_path=plan.output_path,
        command=None,
    )


def _build_docbook_intermediate(
    assembly: AssemblyResult,
    requested_format: OutputFormat,
) -> Path:
    executable = require_tool(
        "asciidoctor",
        requested_format,
        install_hint(assembly.source_format, requested_format, docbook=True),
        tool_resolver=shutil.which,
    )
    output_path = docbook_output_path(assembly)
    command = [
        executable,
        "-a",
        "skip-front-matter",
        "-b",
        "docbook5",
        "-o",
        str(output_path),
        str(assembly.output_path),
    ]
    _run_command(command, requested_format)
    return output_path


def _run_command(command: list[str], requested_format: OutputFormat) -> None:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return

    details = result.stderr.strip() or result.stdout.strip()
    if details:
        raise RenderError(
            f"Cannot build {requested_format.value}: converter exited with code "
            f"{result.returncode}.\n{details}"
        )
    raise RenderError(
        f"Cannot build {requested_format.value}: converter exited with code "
        f"{result.returncode}."
    )
