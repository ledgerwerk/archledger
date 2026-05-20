from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from archledger.assembly import AssemblyResult
from archledger.errors import RenderError
from archledger.formats import OutputFormat
from archledger.model import default_document_filename_for_output_format
from archledger.storage.common import write_text
from archledger.storage.project_config import ProjectConfig

_PANDOC_TARGETS = {
    OutputFormat.DOCX: "docx",
    OutputFormat.MARKDOWN: "gfm",
    OutputFormat.RST: "rst",
    OutputFormat.TEXTILE: "textile",
}


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
            output_path = _resolve_output_path(
                workspace_root,
                build_dir,
                requested_format,
                output,
            )
            if requested_format is OutputFormat.ASCIIDOC:
                outputs.append(_build_asciidoc_output(assembly, output_path))
                continue
            if requested_format in _PANDOC_TARGETS:
                pandoc_command = _pandoc_command_for_format(
                    config,
                    requested_format,
                    output_path,
                    _docbook_output_path(assembly),
                )
                if docbook_path is None:
                    docbook_path = _build_docbook_intermediate(
                        assembly,
                        requested_format,
                    )
                _run_command(pandoc_command, requested_format)
                outputs.append(
                    ConversionResult(
                        format=requested_format.value,
                        output_path=output_path,
                        command=tuple(pandoc_command),
                    )
                )
                continue
            outputs.append(
                _run_direct_converter(
                    requested_format,
                    assembly.output_path,
                    output_path,
                )
            )
    finally:
        if docbook_path is not None and not config.build_keep_intermediate:
            docbook_path.unlink(missing_ok=True)
    return BuildResult(assembled_path=assembly.output_path, outputs=tuple(outputs))


def _resolve_output_path(
    workspace_root: Path,
    build_dir: Path,
    requested_format: OutputFormat,
    output: Path | None,
) -> Path:
    if output is None:
        return build_dir / default_document_filename_for_output_format(
            requested_format.value
        )
    if output.is_absolute():
        return output
    return workspace_root / output


def _build_asciidoc_output(
    assembly: AssemblyResult,
    output_path: Path,
) -> ConversionResult:
    if output_path != assembly.output_path:
        write_text(output_path, assembly.rendered_text)
    return ConversionResult(
        format=OutputFormat.ASCIIDOC.value,
        output_path=output_path,
        command=None,
    )


def _run_direct_converter(
    requested_format: OutputFormat,
    assembly_path: Path,
    output_path: Path,
) -> ConversionResult:
    command = _direct_command_for_format(requested_format, assembly_path, output_path)
    _run_command(command, requested_format)
    return ConversionResult(
        format=requested_format.value,
        output_path=output_path,
        command=tuple(command),
    )


def _direct_command_for_format(
    requested_format: OutputFormat,
    assembly_path: Path,
    output_path: Path,
) -> list[str]:
    if requested_format is OutputFormat.HTML:
        executable = _require_tool(
            "asciidoctor",
            requested_format,
            "Install the Ruby gem `asciidoctor` or disable [build.outputs.html].",
        )
        return [
            executable,
            "-a",
            "skip-front-matter",
            "-b",
            "html5",
            "-o",
            str(output_path),
            str(assembly_path),
        ]
    if requested_format is OutputFormat.PDF:
        executable = _require_tool(
            "asciidoctor-pdf",
            requested_format,
            "Install the Ruby gem `asciidoctor-pdf` or disable [build.outputs.pdf].",
        )
        return [
            executable,
            "-a",
            "skip-front-matter",
            "-o",
            str(output_path),
            str(assembly_path),
        ]
    raise AssertionError(
        f"Unsupported direct conversion format: {requested_format.value}"
    )


def _docbook_output_path(assembly: AssemblyResult) -> Path:
    return assembly.output_path.with_suffix(".docbook.xml")


def _build_docbook_intermediate(
    assembly: AssemblyResult,
    requested_format: OutputFormat,
) -> Path:
    executable = _require_tool(
        "asciidoctor",
        requested_format,
        _pandoc_backed_install_hint(requested_format),
    )
    output_path = _docbook_output_path(assembly)
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


def _pandoc_command_for_format(
    config: ProjectConfig,
    requested_format: OutputFormat,
    output_path: Path,
    docbook_path: Path,
) -> list[str]:
    executable = _require_tool(
        "pandoc",
        requested_format,
        _pandoc_backed_install_hint(requested_format),
    )
    command = [
        executable,
        "-f",
        "docbook",
        "-t",
        _PANDOC_TARGETS[requested_format],
        "-o",
        str(output_path),
        str(docbook_path),
    ]
    if requested_format is OutputFormat.DOCX and config.build_reference_docx.strip():
        command.extend(["--reference-doc", config.build_reference_docx.strip()])
    return command


def _pandoc_backed_install_hint(requested_format: OutputFormat) -> str:
    return (
        "Install the Ruby gem `asciidoctor` and `pandoc` or disable "
        f"[build.outputs.{requested_format.value}]."
    )


def _require_tool(
    executable_name: str,
    requested_format: OutputFormat,
    install_hint: str,
) -> str:
    executable = shutil.which(executable_name)
    if executable is None:
        raise RenderError(
            f"Cannot build {requested_format.value}: "
            f"{executable_name} executable was not found.\n{install_hint}"
        )
    return executable


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
