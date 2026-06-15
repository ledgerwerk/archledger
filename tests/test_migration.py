from __future__ import annotations

import shutil
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
        ["--root", str(tmp_path), "new", "requirement", "Render output"],
    )

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "source", "convert", "--to", "asciidoc"],
    )

    assert result.exit_code == 0
    assert "Planned" in result.stdout
    assert "Re-run with --apply" in result.stdout
    assert not (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    ).exists()


def test_convert_sources_write_requires_pandoc_unless_mixed_is_allowed(
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
            "Render output",
        ],
    )
    monkeypatch.setattr("archledger.migration.shutil.which", lambda name: None)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "source", "convert", "--to", "asciidoc", "--apply"],
    )

    assert result.exit_code == 1
    assert "pandoc" in result.output.lower()
    assert "allow-mixed-body-format" in result.output
    assert not (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    ).exists()


def test_convert_sources_allow_mixed_body_format_without_pandoc(
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
            "Render output",
        ],
    )
    monkeypatch.setattr("archledger.migration.shutil.which", lambda name: None)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "source",
            "convert",
            "--to",
            "asciidoc",
            "--apply",
            "--allow-mixed-body-format",
        ],
    )

    assert result.exit_code == 0
    migrated_path = (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    )
    assert migrated_path.is_file()
    migrated_text = migrated_path.read_text(encoding="utf-8")
    assert "schema_version: 2" in migrated_text
    assert "body_format: markdown" in migrated_text
    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert "config_version = 7" in config_text
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
        ["--root", str(tmp_path), "source", "convert", "--to", "asciidoc", "--apply"],
    )

    assert result.exit_code == 0
    assert seen_commands
    migrated_text = (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    ).read_text(encoding="utf-8")
    assert "body_format: asciidoc" in migrated_text
    assert "Converted body" in migrated_text
    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert "config_version = 7" in config_text
    assert 'default_format = "asciidoc"' in config_text


def test_convert_sources_preserves_v5_tracking_and_build_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", "markdown"],
    )
    assert result.exit_code == 0
    config_path = tmp_path / "archledger.toml"
    config_text = config_path.read_text(encoding="utf-8")
    config_text = config_text.replace(
        'default_output_dir = "build"',
        'default_output_dir = "site-build"',
    )
    config_text = config_text.replace(
        "keep_intermediate = false",
        "keep_intermediate = true",
    )
    config_text = config_text.replace(
        'converter = "auto"',
        'converter = "pandoc"',
    )
    config_text = config_text.replace(
        'pdf_engine = ""',
        'pdf_engine = "tectonic"',
    )
    config_text = config_text.replace(
        'reference_docx = ""',
        'reference_docx = "docs/reference.docx"',
    )
    config_path.write_text(
        config_text + "\n[build.outputs.html]\n"
        'tool = "pandoc"\n'
        "\n[build.outputs.docx]\n"
        'reference_docx = "docs/override.docx"\n',
        encoding="utf-8",
    )
    runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "requirement",
            "Render output",
            "--status",
            "accepted",
        ],
    )
    monkeypatch.setattr(
        "archledger.migration.shutil.which",
        lambda name: "/usr/bin/pandoc",
    )

    def fake_run(
        command: list[str],
        *,
        input: str,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        assert command == ["/usr/bin/pandoc", "-f", "markdown", "-t", "asciidoc"]
        assert input
        return subprocess.CompletedProcess(command, 0, "Converted body\n", "")

    monkeypatch.setattr("archledger.migration.subprocess.run", fake_run)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "source", "convert", "--to", "asciidoc", "--apply"],
    )

    assert result.exit_code == 0
    migrated_config = config_path.read_text(encoding="utf-8")
    assert "config_version = 10" in migrated_config
    assert 'format = "asciidoc"' in migrated_config
    assert 'section_extension = ".adoc"' in migrated_config
    assert 'record_extension = ".adoc"' in migrated_config
    assert "schema_version = 4" in migrated_config
    assert 'default_output = "architecture.adoc"' in migrated_config
    assert 'default_format = "asciidoc"' in migrated_config
    assert 'default_output_dir = "site-build"' in migrated_config
    assert "keep_intermediate = true" in migrated_config
    assert 'converter = "pandoc"' in migrated_config
    assert 'pdf_engine = "tectonic"' in migrated_config
    assert 'reference_docx = "docs/reference.docx"' in migrated_config
    assert "[tracking]" in migrated_config
    assert "[build.outputs.html]" in migrated_config
    assert 'tool = "pandoc"' in migrated_config
    assert "[build.outputs.docx]" in migrated_config
    assert 'reference_docx = "docs/override.docx"' in migrated_config


def test_convert_sources_replace_removes_markdown_files(
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
            "Render output",
        ],
    )
    monkeypatch.setattr(
        "archledger.migration.shutil.which",
        lambda name: "/usr/bin/pandoc",
    )

    def fake_run(
        command: list[str],
        *,
        input: str,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del input, check, capture_output, text
        return subprocess.CompletedProcess(command, 0, "Converted body\n", "")

    monkeypatch.setattr("archledger.migration.subprocess.run", fake_run)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "source",
            "convert",
            "--to",
            "asciidoc",
            "--apply",
            "--replace",
        ],
    )

    assert result.exit_code == 0
    assert not (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.md"
    ).exists()
    assert (
        tmp_path / ".archledger" / "records" / "requirements" / "content-0013.adoc"
    ).is_file()


def init_legacy_project(tmp_path: Path) -> None:
    """Create a legacy project as it existed before profile architecture.

    Runs archledger init, then downgrades the config to config_version 2
    and moves sections from the profile-owned location to the legacy
    <archledger_dir>/sections/ layout.
    """
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert result.exit_code == 0

    # Move sections from profile location to legacy location.
    profile_sections = tmp_path / ".archledger" / "profiles" / "arc42" / "sections"
    legacy_sections = tmp_path / ".archledger" / "sections"
    if profile_sections.is_dir() and not legacy_sections.is_dir():
        shutil.move(str(profile_sections), str(legacy_sections))
        profile_arc42 = tmp_path / ".archledger" / "profiles" / "arc42"
        if profile_arc42.is_dir():
            shutil.rmtree(str(profile_arc42))
        profiles_root = tmp_path / ".archledger" / "profiles"
        if profiles_root.is_dir() and not any(profiles_root.iterdir()):
            profiles_root.rmdir()

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
