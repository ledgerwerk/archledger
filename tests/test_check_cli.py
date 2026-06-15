from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)

runner = CliRunner()


def init_project(tmp_path: Path) -> None:
    """Initialize a project with default (none) segment mode."""
    result = runner.invoke(
        app, ["--root", str(tmp_path), "init", "--source-format", "asciidoc"]
    )
    assert result.exit_code == 0, f"init failed: {result.output}"


def _write_tombstone(tmp_path: Path, record_id: str, order: int) -> Path:
    """Create a minimal archive tombstone file.

    The record ID should use a number >= the project's next_number (starts at 13
    for a fresh init) to avoid triggering ledger-gap errors.
    """
    tombstone_dir = tmp_path / ".archledger" / "archive" / "tombstones"
    tombstone_dir.mkdir(parents=True, exist_ok=True)
    path = tombstone_dir / f"{record_id}.adoc"

    path.write_text(
        "---\n"
        "schema_version: 4\n"
        f"id: {record_id}\n"
        "kind: archive\n"
        "type: archive_tombstone\n"
        f"title: Archived placeholder for missing ledger ID {record_id}\n"
        "status: archived\n"
        "section: risks_and_technical_debt\n"
        f"order: {order}\n"
        "version: 1\n"
        "body_format: asciidoc\n"
        "archived_reason: Created by test setup.\n"
        "---\n\n"
        "This tombstone preserves a ledger number.\n"
    )
    return path


class TestCheckWithArchiveTombstones:
    """Regression: ``archledger check`` and ``build`` must not fail when
    archive tombstone records exist."""

    def test_check_accepts_archive_tombstones(self, tmp_path: Path) -> None:
        init_project(tmp_path)
        # Use IDs 13+ to stay within the project's counter sequence
        _write_tombstone(tmp_path, "archive-0013", 13)
        _write_tombstone(tmp_path, "archive-0014", 14)

        result = runner.invoke(app, ["--root", str(tmp_path), "check"])

        # Must exit 0 — errors block check; warnings are acceptable
        assert result.exit_code == 0, (
            f"check exited {result.exit_code}: {result.output}"
        )
        assert "0 error" in result.output

    def test_build_succeeds_with_archive_tombstones(self, tmp_path: Path) -> None:
        init_project(tmp_path)
        _write_tombstone(tmp_path, "archive-0013", 13)
        _write_tombstone(tmp_path, "archive-0014", 14)

        result = runner.invoke(
            app,
            [
                "--root",
                str(tmp_path),
                "build",
                "--format",
                "asciidoc",
                "--output",
                str(tmp_path / "out.adoc"),
            ],
        )

        assert result.exit_code == 0, (
            f"build exited {result.exit_code}: {result.output}"
        )
        assert (tmp_path / "out.adoc").is_file()


def test_check_preserves_bdd_metadata_but_does_not_validate_it(tmp_path: Path) -> None:
    init_project(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime", "Legacy behavior"],
    )
    assert created.exit_code == 0, created.stdout
    payload = json.loads(created.stdout)
    record_path = Path(payload["result"]["path"])
    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"] = {
        "scenario": "",
        "given": "not-a-list",
        "when": [""],
        "then": [""],
    }
    metadata["sdd"] = {
        "waivers": [
            {"rule": "SDD-OLD", "reason": "legacy"},
        ]
    }
    write_front_matter_document(record_path, metadata, body)

    checked = runner.invoke(app, ["--root", str(tmp_path), "check"])
    assert checked.exit_code == 0, checked.stdout
    lowered = checked.stdout.lower()
    assert "bdd" not in lowered
    assert "gherkin" not in lowered
