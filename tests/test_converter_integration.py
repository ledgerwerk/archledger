from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
def test_markdown_source_builds_html_with_real_pandoc(tmp_path: Path) -> None:
    _init_project(tmp_path, source_format="markdown")

    result = runner.invoke(app, ["--root", str(tmp_path), "build", "--format", "html"])

    assert result.exit_code == 0
    assert (tmp_path / "build" / "architecture.html").is_file()


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("asciidoctor") is None, reason="asciidoctor not installed"
)
def test_asciidoc_source_builds_html_with_real_asciidoctor(tmp_path: Path) -> None:
    _init_project(tmp_path, source_format="asciidoc")

    result = runner.invoke(app, ["--root", str(tmp_path), "build", "--format", "html"])

    assert result.exit_code == 0
    assert (tmp_path / "build" / "architecture.html").is_file()


def _init_project(tmp_path: Path, *, source_format: str) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", source_format],
    )
    assert result.exit_code == 0
