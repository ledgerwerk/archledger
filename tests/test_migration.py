from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_convert_sources_requires_write_for_mutation(tmp_path: Path) -> None:
    init_legacy_project(tmp_path)
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "requirement", "--title", "Render output"],
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "convert-sources", "--to", "asciidoc"],
    )

    assert result.exit_code == 0
    assert "Planned" in result.stdout
    assert "Re-run with --write" in result.stdout
    assert not (
        tmp_path / ".archledger" / "records" / "requirements" / "requirement_0001.adoc"
    ).exists()


def test_convert_sources_writes_adoc_and_updates_config_without_pandoc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_legacy_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "requirement",
            "--title",
            "Render output",
        ],
    )
    monkeypatch.setattr("archledger.migration.shutil.which", lambda name: None)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "convert-sources", "--to", "asciidoc", "--write"],
    )

    assert result.exit_code == 0
    migrated_path = (
        tmp_path / ".archledger" / "records" / "requirements" / "requirement_0001.adoc"
    )
    assert migrated_path.is_file()
    migrated_text = migrated_path.read_text(encoding="utf-8")
    assert "schema_version: 2" in migrated_text
    assert "body_format: markdown" in migrated_text
    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert "config_version = 3" in config_text
    assert 'format = "asciidoc"' in config_text
    assert "pandoc not found" in result.stdout


def test_convert_sources_uses_pandoc_when_available(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_legacy_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "requirement",
            "--title",
            "Render output",
        ],
    )
    monkeypatch.setattr(
        "archledger.migration.shutil.which",
        lambda name: "/usr/bin/pandoc",
    )
    seen_commands: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        input: str,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        seen_commands.append(command)
        assert command == ["/usr/bin/pandoc", "-f", "markdown", "-t", "asciidoc"]
        assert input
        return subprocess.CompletedProcess(command, 0, "Converted body\n", "")

    monkeypatch.setattr("archledger.migration.subprocess.run", fake_run)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "convert-sources", "--to", "asciidoc", "--write"],
    )

    assert result.exit_code == 0
    assert seen_commands
    migrated_text = (
        tmp_path / ".archledger" / "records" / "requirements" / "requirement_0001.adoc"
    ).read_text(encoding="utf-8")
    assert "body_format: asciidoc" in migrated_text
    assert "Converted body" in migrated_text


def test_convert_sources_replace_removes_markdown_files(tmp_path: Path) -> None:
    init_legacy_project(tmp_path)
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "requirement",
            "--title",
            "Render output",
        ],
    )

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "convert-sources",
            "--to",
            "asciidoc",
            "--write",
            "--replace",
        ],
    )

    assert result.exit_code == 0
    assert not (
        tmp_path / ".archledger" / "records" / "requirements" / "requirement_0001.md"
    ).exists()
    assert (
        tmp_path / ".archledger" / "records" / "requirements" / "requirement_0001.adoc"
    ).is_file()


def init_legacy_project(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert result.exit_code == 0

    (tmp_path / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 2",
                'archledger_dir = ".archledger"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
                "[build]",
                'default_output = "architecture.md"',
                "include_draft = false",
                "include_superseded = false",
                "strict = false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for path in (tmp_path / ".archledger" / "sections").glob("*.adoc"):
        path.rename(path.with_suffix(".md"))
