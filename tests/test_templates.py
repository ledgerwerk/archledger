from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.model import (
    RECORD_TYPE_TO_TEMPLATE,
    VALID_SOURCE_FORMATS,
    document_template_name_for_source_format,
    record_template_name_for_source_format,
)

runner = CliRunner()


def test_all_record_templates_are_bundled() -> None:
    template_root = Path("archledger/templates")
    for source_format in VALID_SOURCE_FORMATS:
        assert (
            template_root / document_template_name_for_source_format(source_format)
        ).is_file()
    for source_format in VALID_SOURCE_FORMATS:
        for record_type in RECORD_TYPE_TO_TEMPLATE:
            template_name = record_template_name_for_source_format(
                record_type,
                source_format,
            )
            assert (template_root / "records" / template_name).is_file()


def test_all_markdown_templates_include_schema_version_date_body_format() -> None:
    template_root = Path("archledger/templates/records")
    for path in sorted(template_root.glob("*.md.j2")):
        text = path.read_text(encoding="utf-8")
        assert "schema_version: 2" in text, path.name
        assert "date: {{ date | tojson }}" in text, path.name
        assert "body_format: markdown" in text, path.name
        assert "created_at: {{ created_at | tojson }}" in text, path.name
        assert "updated_at: {{ updated_at | tojson }}" in text, path.name


def test_all_asciidoc_templates_include_schema_version_date_body_format() -> None:
    template_root = Path("archledger/templates/records")
    for path in sorted(template_root.glob("*.adoc.j2")):
        text = path.read_text(encoding="utf-8")
        assert "schema_version: 2" in text, path.name
        assert "date: {{ date | tojson }}" in text, path.name
        assert "body_format: asciidoc" in text, path.name
        assert "created_at: {{ created_at | tojson }}" in text, path.name
        assert "updated_at: {{ updated_at | tojson }}" in text, path.name


def test_section_templates_include_schema_version_date_body_format(
    tmp_path: Path,
) -> None:
    markdown_root = tmp_path / "markdown"
    asciidoc_root = tmp_path / "asciidoc"
    assert (
        runner.invoke(
            app,
            ["--root", str(markdown_root), "init", "--source-format", "markdown"],
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(
            app,
            ["--root", str(asciidoc_root), "init", "--source-format", "asciidoc"],
        ).exit_code
        == 0
    )

    markdown_section = (
        markdown_root / ".archledger" / "sections" / "01_introduction_and_goals.md"
    ).read_text(encoding="utf-8")
    asciidoc_section = (
        asciidoc_root / ".archledger" / "sections" / "01_introduction_and_goals.adoc"
    ).read_text(encoding="utf-8")

    for text, body_format in (
        (markdown_section, "markdown"),
        (asciidoc_section, "asciidoc"),
    ):
        assert "schema_version: 2" in text
        assert 'date: "' in text
        assert f"body_format: {body_format}" in text
        assert 'created_at: "' in text
        assert 'updated_at: "' in text


def test_new_succeeds_for_every_record_type(tmp_path: Path) -> None:
    assert runner.invoke(app, ["--root", str(tmp_path), "init"]).exit_code == 0
    for cli_kind in [
        "requirement",
        "stakeholder",
        "quality-goal",
        "constraint",
        "context-interface",
        "strategy-item",
        "white-box",
        "black-box",
        "interface",
        "runtime",
        "infrastructure",
        "concept",
        "adr",
        "quality-requirement",
        "quality-scenario",
        "risk",
        "glossary-term",
    ]:
        result = runner.invoke(
            app,
            [
                "--root",
                str(tmp_path),
                "new",
                cli_kind,
                "--title",
                cli_kind,
                "--status",
                "proposed",
            ],
        )
        assert result.exit_code == 0, result.output


def test_build_succeeds_after_init(tmp_path: Path) -> None:
    assert runner.invoke(app, ["--root", str(tmp_path), "init"]).exit_code == 0

    result = runner.invoke(app, ["--root", str(tmp_path), "build"])

    assert result.exit_code == 0
