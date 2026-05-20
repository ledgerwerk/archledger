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
