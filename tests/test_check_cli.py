from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

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
        "schema_version: 2\n"
        f"id: {record_id}\n"
        "type: archive_tombstone\n"
        f"title: Archived placeholder for missing ledger ID {record_id}\n"
        "status: archived\n"
        "section: risks_and_technical_debt\n"
        f"order: {order}\n"
        'date: "2026-06-07"\n'
        "body_format: asciidoc\n"
        'created_at: "2026-06-07T00:00:00Z"\n'
        'updated_at: "2026-06-07T00:00:00Z"\n'
        'archived_at: "2026-06-07T00:00:00Z"\n'
        "archived_reason: Created by test setup.\n"
        "---\n"
        "\n"
        "This tombstone preserves a ledger number.\n"
    )
    return path


class TestCheckWithArchiveTombstones:
    """Regression: ``archledger check`` and ``build`` must not fail when
    archive tombstone records exist."""

    def test_check_accepts_archive_tombstones(self, tmp_path: Path) -> None:
        init_project(tmp_path)
        # Use IDs 13+ to stay within the project's counter sequence
        _write_tombstone(tmp_path, "al_0013", 13)
        _write_tombstone(tmp_path, "al_0014", 14)

        result = runner.invoke(app, ["--root", str(tmp_path), "check"])

        # Must exit 0 — errors block check; warnings are acceptable
        assert result.exit_code == 0, (
            f"check exited {result.exit_code}: {result.output}"
        )
        assert "0 error" in result.output

    def test_build_succeeds_with_archive_tombstones(self, tmp_path: Path) -> None:
        init_project(tmp_path)
        _write_tombstone(tmp_path, "al_0013", 13)
        _write_tombstone(tmp_path, "al_0014", 14)

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
