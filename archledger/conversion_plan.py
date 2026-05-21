from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from archledger.assembly import AssemblyResult
from archledger.errors import RenderError
from archledger.formats import OutputFormat
from archledger.storage.project_config import ProjectConfig

ToolResolver = Callable[[str], str | None]

_PANDOC_TARGETS = {
    OutputFormat.ASCIIDOC: "asciidoc",
    OutputFormat.DOCX: "docx",
    OutputFormat.HTML: "html5",
    OutputFormat.MARKDOWN: "gfm",
    OutputFormat.RST: "rst",
    OutputFormat.TEXTILE: "textile",
}


@dataclass(frozen=True, slots=True)
class ConversionPlan:
    requested_format: OutputFormat
    output_path: Path
    command: list[str] | None = None
    native_copy: bool = False
    requires_docbook: bool = False


def plan_conversion(
    config: ProjectConfig,
    assembly: AssemblyResult,
    requested_format: OutputFormat,
    output_path: Path,
    *,
    tool_resolver: ToolResolver | None = None,
) -> ConversionPlan:
    if tool_resolver is None:
        tool_resolver = shutil.which

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
                tool_resolver=tool_resolver,
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
                        tool_resolver=tool_resolver,
                    ),
                )
            return ConversionPlan(
                requested_format=requested_format,
                output_path=output_path,
                command=_direct_asciidoctor_command(
                    requested_format,
                    assembly.output_path,
                    output_path,
                    tool_resolver=tool_resolver,
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
                    docbook_output_path(assembly),
                    from_format="docbook",
                    tool_resolver=tool_resolver,
                ),
                requires_docbook=True,
            )

    raise RenderError(
        f"Cannot build {requested_format.value} from {assembly.source_format} source."
    )

def docbook_output_path(assembly: AssemblyResult) -> Path:
    return assembly.output_path.with_suffix(".docbook.xml")


def install_hint(
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


def require_tool(
    executable_name: str,
    requested_format: OutputFormat,
    install_message: str,
    *,
    tool_resolver: ToolResolver | None = None,
) -> str:
    if tool_resolver is None:
        tool_resolver = shutil.which
    executable = tool_resolver(executable_name)
    if executable is None:
        raise RenderError(
            f"Cannot build {requested_format.value}: "
            f"{executable_name} executable was not found.\n{install_message}"
        )
    return executable


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
    *,
    tool_resolver: ToolResolver,
) -> list[str]:
    if requested_format is OutputFormat.HTML:
        executable = require_tool(
            "asciidoctor",
            requested_format,
            "Install the Ruby gem `asciidoctor` or disable [build.outputs.html].",
            tool_resolver=tool_resolver,
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
        executable = require_tool(
            "asciidoctor-pdf",
            requested_format,
            "Install the Ruby gem `asciidoctor-pdf` or disable [build.outputs.pdf].",
            tool_resolver=tool_resolver,
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


def _pandoc_command(
    config: ProjectConfig,
    requested_format: OutputFormat,
    output_path: Path,
    input_path: Path,
    *,
    from_format: str,
    tool_resolver: ToolResolver,
) -> list[str]:
    executable = require_tool(
        "pandoc",
        requested_format,
        install_hint(from_format, requested_format, docbook=from_format == "docbook"),
        tool_resolver=tool_resolver,
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
    reference_docx = _reference_docx(config, requested_format)
    if requested_format is OutputFormat.DOCX and reference_docx:
        command.extend(["--reference-doc", reference_docx])
    command.append(str(input_path))
    return command


def _pdf_engine(config: ProjectConfig, requested_format: OutputFormat) -> str:
    output_config = config.build_outputs.get(requested_format.value, {})
    configured = output_config.get("pdf_engine")
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    return config.build_pdf_engine


def _reference_docx(config: ProjectConfig, requested_format: OutputFormat) -> str:
    output_config = config.build_outputs.get(requested_format.value, {})
    configured = output_config.get("reference_docx")
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    return config.build_reference_docx.strip()
