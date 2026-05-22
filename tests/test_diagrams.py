from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from archledger.assembly import AssemblyResult
from archledger.cli import app
from archledger.diagrams import materialize_diagrams_for_conversion
from archledger.errors import RenderError
from archledger.formats import OutputFormat
from archledger.storage.project_config import ProjectConfig

runner = CliRunner()


def test_check_warns_for_diagram_without_markdown_mermaid_block(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "diagram",
            "Runtime login flow",
            "--status",
            "accepted",
            "--diagram-type",
            "mermaid",
        ],
    )
    diagram_path = tmp_path / ".archledger" / "records" / "diagrams" / "al_0013.md"
    diagram_path.write_text(
        diagram_path.read_text(encoding="utf-8").replace(
            "```mermaid\n"
            "flowchart LR\n  A[Start] --> B[Describe architecture flow]\n"
            "```",
            "No mermaid block here.",
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    warnings = json.loads(result.stdout)["result"]["warnings"]
    messages = [item["message"] for item in warnings]
    assert (
        "Diagram al_0013 markdown body is missing a fenced mermaid block." in messages
    )


def test_check_warns_for_diagram_without_asciidoc_mermaid_block(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="asciidoc")
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "diagram",
            "Runtime login flow",
            "--status",
            "accepted",
            "--diagram-type",
            "mermaid",
        ],
    )
    diagram_path = tmp_path / ".archledger" / "records" / "diagrams" / "al_0013.adoc"
    diagram_path.write_text(
        diagram_path.read_text(encoding="utf-8").replace(
            "[mermaid]\n....\n"
            "flowchart LR\n  A[Start] --> B[Describe architecture flow]\n"
            "....",
            "No mermaid block here.",
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    warnings = json.loads(result.stdout)["result"]["warnings"]
    messages = [item["message"] for item in warnings]
    assert "Diagram al_0013 asciidoc body is missing a [mermaid] block." in messages


def test_check_warns_for_empty_markdown_mermaid_block(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "diagram",
            "Runtime login flow",
            "--status",
            "accepted",
            "--diagram-type",
            "mermaid",
        ],
    )
    diagram_path = tmp_path / ".archledger" / "records" / "diagrams" / "al_0013.md"
    diagram_path.write_text(
        diagram_path.read_text(encoding="utf-8").replace(
            "```mermaid\n"
            "flowchart LR\n  A[Start] --> B[Describe architecture flow]\n"
            "```",
            "```mermaid\n\n```",
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    warnings = json.loads(result.stdout)["result"]["warnings"]
    messages = [item["message"] for item in warnings]
    assert "Diagram al_0013 mermaid block is empty." in messages


def init_project(tmp_path: Path, source_format: str) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", source_format],
    )
    assert result.exit_code == 0


def test_materialize_markdown_mermaid_block_rewrites_to_image(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assembly = AssemblyResult(
        output_path=tmp_path / "architecture.md",
        rendered_text="```mermaid\nflowchart LR\n  A --> B\n```",
        source_format="markdown",
    )
    config = ProjectConfig(
        config_version=5,
        archledger_dir=".archledger",
        project_uuid="12345678-1234-1234-1234-123456789abc",
        project_name="demo",
        diagram_enabled=True,
        diagram_renderer="mermaid-cli",
    )
    monkeypatch.setattr(
        "archledger.diagrams.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = materialize_diagrams_for_conversion(
        config,
        build_dir=tmp_path / "build",
        assembly=assembly,
        requested_format=OutputFormat.HTML,
        tool_resolver=lambda _: "/usr/bin/mmdc",
    )

    assert result is not None
    rewritten = result.input_path.read_text(encoding="utf-8")
    assert "![Mermaid diagram](diagrams/mermaid-" in rewritten
    assert rewritten.endswith(".svg)")


def test_materialize_asciidoc_mermaid_block_rewrites_to_image(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assembly = AssemblyResult(
        output_path=tmp_path / "architecture.adoc",
        rendered_text="[mermaid]\n....\nflowchart LR\n  A --> B\n....",
        source_format="asciidoc",
    )
    config = ProjectConfig(
        config_version=5,
        archledger_dir=".archledger",
        project_uuid="12345678-1234-1234-1234-123456789abc",
        project_name="demo",
        diagram_enabled=True,
        diagram_renderer="mermaid-cli",
    )
    monkeypatch.setattr(
        "archledger.diagrams.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    result = materialize_diagrams_for_conversion(
        config,
        build_dir=tmp_path / "build",
        assembly=assembly,
        requested_format=OutputFormat.PDF,
        tool_resolver=lambda _: "/usr/bin/mmdc",
    )

    assert result is not None
    rewritten = result.input_path.read_text(encoding="utf-8")
    assert "image::diagrams/mermaid-" in rewritten
    assert rewritten.endswith(".svg[Mermaid diagram]")


def test_diagram_asset_names_are_content_hash_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = "```mermaid\nflowchart LR\n  A --> B\n```"
    assembly_a = AssemblyResult(
        output_path=tmp_path / "a.md",
        rendered_text=source,
        source_format="markdown",
    )
    assembly_b = AssemblyResult(
        output_path=tmp_path / "b.md",
        rendered_text=source,
        source_format="markdown",
    )
    config = ProjectConfig(
        config_version=5,
        archledger_dir=".archledger",
        project_uuid="12345678-1234-1234-1234-123456789abc",
        project_name="demo",
        diagram_enabled=True,
        diagram_renderer="mermaid-cli",
    )
    monkeypatch.setattr(
        "archledger.diagrams.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )

    first = materialize_diagrams_for_conversion(
        config,
        build_dir=tmp_path / "build",
        assembly=assembly_a,
        requested_format=OutputFormat.HTML,
        tool_resolver=lambda _: "/usr/bin/mmdc",
    )
    second = materialize_diagrams_for_conversion(
        config,
        build_dir=tmp_path / "build",
        assembly=assembly_b,
        requested_format=OutputFormat.HTML,
        tool_resolver=lambda _: "/usr/bin/mmdc",
    )
    assert first is not None
    assert second is not None
    rewritten_first = first.input_path.read_text(encoding="utf-8")
    rewritten_second = second.input_path.read_text(encoding="utf-8")
    assert rewritten_first == rewritten_second


def test_mermaid_cli_missing_has_actionable_error(tmp_path: Path) -> None:
    assembly = AssemblyResult(
        output_path=tmp_path / "architecture.md",
        rendered_text="```mermaid\nflowchart LR\n  A --> B\n```",
        source_format="markdown",
    )
    config = ProjectConfig(
        config_version=5,
        archledger_dir=".archledger",
        project_uuid="12345678-1234-1234-1234-123456789abc",
        project_name="demo",
        diagram_enabled=True,
        diagram_renderer="mermaid-cli",
    )

    with pytest.raises(RenderError) as excinfo:
        materialize_diagrams_for_conversion(
            config,
            build_dir=tmp_path / "build",
            assembly=assembly,
            requested_format=OutputFormat.HTML,
            tool_resolver=lambda _: None,
        )
    assert "mmdc executable was not found" in str(excinfo.value)


def test_new_diagram_defaults_to_text_type(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "diagram", "Architecture overview"],
    )
    diagram_path = tmp_path / ".archledger" / "records" / "diagrams" / "al_0013.md"
    content = diagram_path.read_text(encoding="utf-8")
    assert 'diagram_type: "text"' in content
    assert "```textdiagram" in content


def test_new_diagram_uses_configured_default_type(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'default_type = "text"', 'default_type = "unicode"'
        ),
        encoding="utf-8",
    )
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "diagram", "Unicode diagram"],
    )
    diagram_path = tmp_path / ".archledger" / "records" / "diagrams" / "al_0013.md"
    content = diagram_path.read_text(encoding="utf-8")
    assert 'diagram_type: "unicode"' in content
    assert "```textdiagram" in content


def test_check_accepts_markdown_textdiagram_block(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "diagram", "Text diagram"],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    warnings = json.loads(result.stdout)["result"]["warnings"]
    messages = [item["message"] for item in warnings]
    assert not any("missing a fenced" in m and "al_0013" in m for m in messages)


def test_check_accepts_markdown_unicode_textdiagram_block(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "diagram",
            "Unicode diagram",
            "--diagram-type",
            "unicode",
        ],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    warnings = json.loads(result.stdout)["result"]["warnings"]
    messages = [item["message"] for item in warnings]
    assert not any("missing a fenced" in m and "al_0013" in m for m in messages)


def test_check_accepts_asciidoc_source_text_block(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="asciidoc")
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "diagram", "AsciiDoc text diagram"],
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    warnings = json.loads(result.stdout)["result"]["warnings"]
    messages = [item["message"] for item in warnings]
    assert not any("missing" in m and "al_0013" in m for m in messages)


def test_check_warns_for_empty_textdiagram_block(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "diagram", "Empty text diagram"],
    )
    diagram_path = tmp_path / ".archledger" / "records" / "diagrams" / "al_0013.md"
    diagram_path.write_text(
        diagram_path.read_text(encoding="utf-8").replace(
            "```textdiagram\n"
            "┌─────────┐     ┌──────────┐\n"
            "│ Source  │ ──> │ Output   │\n"
            "└─────────┘     └──────────┘\n"
            "```",
            "```textdiagram\n\n```",
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    warnings = json.loads(result.stdout)["result"]["warnings"]
    messages = [item["message"] for item in warnings]
    assert "Diagram al_0013 text block is empty." in messages


def test_check_warns_for_overwide_textdiagram_line(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "diagram", "Wide text diagram"],
    )
    diagram_path = tmp_path / ".archledger" / "records" / "diagrams" / "al_0013.md"
    wide_line = "─" * 130
    diagram_path.write_text(
        diagram_path.read_text(encoding="utf-8").replace(
            "```textdiagram\n"
            "┌─────────┐     ┌──────────┐\n"
            "│ Source  │ ──> │ Output   │\n"
            "└─────────┘     └──────────┘\n"
            "```",
            f"```textdiagram\n{wide_line}\n```",
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    warnings = json.loads(result.stdout)["result"]["warnings"]
    messages = [item["message"] for item in warnings]
    assert any("exceeding 120 characters" in m and "al_0013" in m for m in messages)


def test_mermaid_still_supported_when_requested(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "diagram",
            "Sequence diagram",
            "--diagram-type",
            "mermaid",
        ],
    )
    diagram_path = tmp_path / ".archledger" / "records" / "diagrams" / "al_0013.md"
    content = diagram_path.read_text(encoding="utf-8")
    assert 'diagram_type: "mermaid"' in content
    assert "```mermaid" in content

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "check"])

    assert result.exit_code == 0
    warnings = json.loads(result.stdout)["result"]["warnings"]
    messages = [item["message"] for item in warnings]
    assert not any("unsupported diagram_type" in m for m in messages)
