from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.model import (
    CLI_KIND_ALIASES,
    RECORD_TYPE_TO_DEFAULT_SECTION,
    RECORD_TYPE_TO_DIR,
    RECORD_TYPE_TO_TEMPLATE,
    RECORD_TYPES,
    VALID_SOURCE_FORMATS,
    document_template_name_for_source_format,
    record_template_name_for_source_format,
)
from archledger.record_types import RecordContextInput

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


def test_record_type_registry_preserves_legacy_maps() -> None:
    assert {
        kind: spec.directory for kind, spec in RECORD_TYPES.items()
    } == RECORD_TYPE_TO_DIR
    assert {
        kind: spec.default_section for kind, spec in RECORD_TYPES.items()
    } == RECORD_TYPE_TO_DEFAULT_SECTION
    assert {
        kind: f"{spec.template_basename}.md.j2" for kind, spec in RECORD_TYPES.items()
    } == RECORD_TYPE_TO_TEMPLATE
    assert {
        alias: kind for kind, spec in RECORD_TYPES.items() for alias in spec.aliases
    } == CLI_KIND_ALIASES


def test_record_type_registry_covers_all_templates() -> None:
    template_root = Path("archledger/templates/records")
    markdown_templates = {
        path.name.removesuffix(".md.j2") for path in template_root.glob("*.md.j2")
    }
    asciidoc_templates = {
        path.name.removesuffix(".adoc.j2") for path in template_root.glob("*.adoc.j2")
    }
    registry_templates = {spec.template_basename for spec in RECORD_TYPES.values()}

    assert registry_templates == markdown_templates
    assert registry_templates == asciidoc_templates


def test_all_registry_entries_have_context_factories_or_empty_defaults() -> None:
    for spec in RECORD_TYPES.values():
        context = spec.context_factory(
            RecordContextInput(
                title="Demo",
                status=spec.default_status,
                section=spec.default_section,
                parent=None,
                kwargs={},
            )
        )
        assert isinstance(context, dict)


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
        markdown_root / ".archledger" / "sections" / "al_0001.md"
    ).read_text(encoding="utf-8")
    asciidoc_section = (
        asciidoc_root / ".archledger" / "sections" / "al_0001.adoc"
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
        "diagram",
        "glossary-term",
    ]:
        result = runner.invoke(
            app,
            [
                "--root",
                str(tmp_path),
                "new",
                cli_kind,
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
