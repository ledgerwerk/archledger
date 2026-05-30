from __future__ import annotations

import hashlib
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from archledger.assembly import AssemblyResult
from archledger.errors import RenderError
from archledger.formats import OutputFormat
from archledger.storage.common import write_text
from archledger.storage.project_config import ProjectConfig

_MARKDOWN_MERMAID_BLOCK = re.compile(
    r"```mermaid\s*\n(.*?)\n```",
    flags=re.IGNORECASE | re.DOTALL,
)
_ASCIIDOC_MERMAID_BLOCK = re.compile(
    r"\[mermaid\]\s*\n\.\.\.\.\s*\n(.*?)\n\.\.\.\.",
    flags=re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class DiagramBlock:
    id: str
    diagram_type: str
    source: str
    caption: str
    source_record_id: str | None
    source_format: str


@dataclass(frozen=True, slots=True)
class MaterializedDiagramDocument:
    input_path: Path
    cleanup_paths: tuple[Path, ...]


def materialize_diagrams_for_conversion(
    config: ProjectConfig,
    *,
    build_dir: Path,
    assembly: AssemblyResult,
    requested_format: OutputFormat,
    tool_resolver: Callable[[str], str | None] | None = None,
) -> MaterializedDiagramDocument | None:
    if not config.diagram_enabled:
        return None
    renderer = config.diagram_renderer
    if renderer == "pass-through" or renderer == "asciidoctor-diagram":
        return None
    if renderer == "kroki":
        raise RenderError(
            "Cannot materialize Mermaid diagrams with renderer=kroki yet. "
            "Use pass-through, asciidoctor-diagram, or mermaid-cli."
        )
    if renderer != "mermaid-cli":
        raise RenderError(f"Unsupported diagram renderer: {renderer}")

    image_format = _image_format_for_requested_output(config, requested_format)
    diagram_output_dir = build_dir / config.diagram_output_dir
    diagram_output_dir.mkdir(parents=True, exist_ok=True)

    if assembly.source_format == "markdown":
        rewritten_text, cleanup_paths = _materialize_markdown_blocks(
            assembly.rendered_text,
            diagram_output_dir,
            image_format=image_format,
            requested_format=requested_format,
            tool_resolver=tool_resolver,
        )
    elif assembly.source_format == "asciidoc":
        rewritten_text, cleanup_paths = _materialize_asciidoc_blocks(
            assembly.rendered_text,
            diagram_output_dir,
            image_format=image_format,
            requested_format=requested_format,
            tool_resolver=tool_resolver,
        )
    else:
        return None

    if rewritten_text == assembly.rendered_text:
        return None

    temp_path = assembly.output_path.with_name(
        f"{assembly.output_path.stem}.diagrams{assembly.output_path.suffix}"
    )
    write_text(temp_path, rewritten_text)
    return MaterializedDiagramDocument(
        input_path=temp_path,
        cleanup_paths=(temp_path, *cleanup_paths),
    )


def _materialize_blocks(
    text: str,
    diagram_output_dir: Path,
    pattern: re.Pattern[str],
    *,
    image_format: str,
    requested_format: OutputFormat,
    tool_resolver: Callable[[str], str | None] | None,
    replacement_for_asset: Callable[[str], str],
) -> tuple[str, tuple[Path, ...]]:
    cleanup_paths: list[Path] = []
    replacements: dict[str, str] = {}
    for match in pattern.finditer(text):
        source = match.group(1).strip()
        if not source:
            continue
        asset_path, source_path = _render_mermaid_asset(
            source,
            diagram_output_dir,
            image_format=image_format,
            requested_format=requested_format,
            tool_resolver=tool_resolver,
        )
        cleanup_paths.append(source_path)
        relative_asset = asset_path.relative_to(diagram_output_dir.parent).as_posix()
        replacements[match.group(0)] = replacement_for_asset(relative_asset)
    rewritten = text
    for original, replacement in replacements.items():
        rewritten = rewritten.replace(original, replacement)
    return rewritten, tuple(cleanup_paths)


def _materialize_markdown_blocks(
    text: str,
    diagram_output_dir: Path,
    *,
    image_format: str,
    requested_format: OutputFormat,
    tool_resolver: Callable[[str], str | None] | None,
) -> tuple[str, tuple[Path, ...]]:
    return _materialize_blocks(
        text,
        diagram_output_dir,
        _MARKDOWN_MERMAID_BLOCK,
        image_format=image_format,
        requested_format=requested_format,
        tool_resolver=tool_resolver,
        replacement_for_asset=lambda rel: f"![Mermaid diagram]({rel})",
    )


def _materialize_asciidoc_blocks(
    text: str,
    diagram_output_dir: Path,
    *,
    image_format: str,
    requested_format: OutputFormat,
    tool_resolver: Callable[[str], str | None] | None,
) -> tuple[str, tuple[Path, ...]]:
    return _materialize_blocks(
        text,
        diagram_output_dir,
        _ASCIIDOC_MERMAID_BLOCK,
        image_format=image_format,
        requested_format=requested_format,
        tool_resolver=tool_resolver,
        replacement_for_asset=lambda rel: f"image::{rel}[Mermaid diagram]",
    )


def _render_mermaid_asset(
    source: str,
    diagram_output_dir: Path,
    *,
    image_format: str,
    requested_format: OutputFormat,
    tool_resolver: Callable[[str], str | None] | None,
) -> tuple[Path, Path]:
    source_hash = _diagram_hash(source)
    source_path = diagram_output_dir / f"mermaid-{source_hash}.mmd"
    asset_path = diagram_output_dir / f"mermaid-{source_hash}.{image_format}"
    write_text(source_path, source.strip() + "\n")
    if asset_path.exists():
        return asset_path, source_path

    mmdc = _resolve_tool(tool_resolver, "mmdc")
    result = subprocess.run(
        [mmdc, "-i", str(source_path), "-o", str(asset_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RenderError(
            f"Cannot build {requested_format.value}: mmdc exited with code "
            f"{result.returncode}.\n{details}"
        )
    return asset_path, source_path


def _resolve_tool(
    tool_resolver: Callable[[str], str | None] | None, executable: str
) -> str:
    resolver = tool_resolver if tool_resolver is not None else _default_tool_resolver
    resolved = resolver(executable)
    if resolved is None:
        raise RenderError(
            "Cannot materialize Mermaid diagrams: mmdc executable was not found.\n"
            "Install @mermaid-js/mermaid-cli (mmdc) or set [diagrams].renderer = "
            '"pass-through".'
        )
    return str(resolved)


def _default_tool_resolver(executable: str) -> str | None:
    from shutil import which

    return which(executable)


def _diagram_hash(source: str) -> str:
    return hashlib.sha256(source.strip().encode("utf-8")).hexdigest()[:12]


def _image_format_for_requested_output(
    config: ProjectConfig,
    requested_format: OutputFormat,
) -> str:
    if requested_format is OutputFormat.DOCX:
        return "png"
    return config.diagram_image_format
