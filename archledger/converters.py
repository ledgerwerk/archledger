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
    OutputFormat.ASCIIDOC: "asciidoc",
    OutputFormat.DOCX: "docx",
    OutputFormat.HTML: "html5",
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


@dataclass(frozen=True, slots=True)
class ConversionPlan:
    requested_format: OutputFormat
    output_path: Path
    command: list[str] | None = None
    native_copy: bool = False
    requires_docbook: bool = False


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
            plan = _conversion_plan(
                config,
                assembly,
                requested_format,
                output_path,
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


def _conversion_plan(
    config: ProjectConfig,
    assembly: AssemblyResult,
    requested_format: OutputFormat,
    output_path: Path,
) -> ConversionPlan:
    source_format = assembly.source_format
    if source_format == "markdown":
        if requested_format is OutputFormat.MARKDOWN:
            return ConversionPlan(
                requested_format=requested_format,
                output_path=output_path,
                native_copy=True,
            )
        return ConversionPlan(
            requested_format=requested_format,
            output_path=output_path,
            command=_pandoc_command(
                config,
                requested_format,
                output_path,
                assembly.output_path,
                from_format="gfm",
            ),
        )

    if source_format == "asciidoc":
        if requested_format is OutputFormat.ASCIIDOC:
            return ConversionPlan(
                requested_format=requested_format,
                output_path=output_path,
                native_copy=True,
            )
        selected_converter = _selected_converter(config, requested_format)
        if requested_format in {OutputFormat.HTML, OutputFormat.PDF}:
            if selected_converter == "pandoc":
                return ConversionPlan(
                    requested_format=requested_format,
                    output_path=output_path,
                    command=_pandoc_command(
                        config,
                        requested_format,
                        output_path,
                        assembly.output_path,
                        from_format="asciidoc",
                    ),
                )
            return ConversionPlan(
                requested_format=requested_format,
                output_path=output_path,
                command=_direct_asciidoctor_command(
                    requested_format,
                    assembly.output_path,
                    output_path,
                ),
            )
        if requested_format in {
            OutputFormat.DOCX,
            OutputFormat.MARKDOWN,
            OutputFormat.RST,
            OutputFormat.TEXTILE,
        }:
            return ConversionPlan(
                requested_format=requested_format,
                output_path=output_path,
                command=_pandoc_command(
                    config,
                    requested_format,
                    output_path,
                    _docbook_output_path(assembly),
                    from_format="docbook",
                ),
                requires_docbook=True,
            )

    raise RenderError(
        f"Cannot build {requested_format.value} from {assembly.source_format} source."
    )


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


def _selected_converter(config: ProjectConfig, requested_format: OutputFormat) -> str:
    output_config = config.build_outputs.get(requested_format.value, {})
    configured = output_config.get("tool")
    if isinstance(configured, str) and configured.strip():
        return configured.strip().lower()
    return config.build_converter


def _direct_asciidoctor_command(
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
        f"Unsupported direct AsciiDoc conversion format: {requested_format.value}"
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
        _install_hint(assembly.source_format, requested_format, docbook=True),
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


def _pandoc_command(
    config: ProjectConfig,
    requested_format: OutputFormat,
    output_path: Path,
    input_path: Path,
    *,
    from_format: str,
) -> list[str]:
    executable = _require_tool(
        "pandoc",
        requested_format,
        _install_hint(from_format, requested_format, docbook=from_format == "docbook"),
    )
    command = [
        executable,
        "-f",
        from_format,
    ]
    target = _PANDOC_TARGETS.get(requested_format)
    if target is not None:
        command.extend(["-t", target])
    command.extend(["-o", str(output_path)])
    pdf_engine = _pdf_engine(config, requested_format)
    if requested_format is OutputFormat.PDF and pdf_engine:
        command.extend(["--pdf-engine", pdf_engine])
    if requested_format is OutputFormat.DOCX and config.build_reference_docx.strip():
        command.extend(["--reference-doc", config.build_reference_docx.strip()])
    command.append(str(input_path))
    return command


def _pdf_engine(config: ProjectConfig, requested_format: OutputFormat) -> str:
    output_config = config.build_outputs.get(requested_format.value, {})
    configured = output_config.get("pdf_engine")
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    return config.build_pdf_engine


def _install_hint(
    source_format: str,
    requested_format: OutputFormat,
    *,
    docbook: bool = False,
) -> str:
    if docbook:
        return (
            "Install the Ruby gem `asciidoctor` and `pandoc` or disable "
            f"[build.outputs.{requested_format.value}]."
        )
    if source_format == "gfm":
        return f"Install `pandoc` or disable [build.outputs.{requested_format.value}]."
    if source_format == "asciidoc":
        return (
            "Install `pandoc` or configure [build.outputs."
            f'{requested_format.value}] tool = "asciidoctor".'
        )
    return f"Install the required converter for {requested_format.value} output."


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
