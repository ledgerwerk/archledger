from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)
from archledger.storage.paths import resolve_project_paths

runner = CliRunner()


def init_project(tmp_path: Path, source_format: str = "asciidoc") -> None:
    """Initialize a project with the requested source format."""
    result = runner.invoke(
        app, ["--root", str(tmp_path), "init", "--source-format", source_format]
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


def _author_section_prose(tmp_path: Path, *, except_section: str | None = None) -> None:
    paths, config, warnings = resolve_project_paths(tmp_path)
    assert not warnings
    for path in paths.sections_dir.glob(f"*{config.section_extension}"):
        metadata, _ = read_front_matter_document(path)
        if metadata["section"] != except_section:
            write_front_matter_document(
                path, metadata, "Authored architecture prose.\n"
            )


def _check_payload(tmp_path: Path, *, strict: bool = False) -> tuple[int, dict]:
    args = ["--root", str(tmp_path), "--json", "check"]
    if strict:
        args.append("--strict")
    result = runner.invoke(app, args)
    return result.exit_code, json.loads(result.stdout)


def _findings(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    if payload["ok"]:
        return cast(list[dict[str, Any]], payload["result"][key])
    return cast(list[dict[str, Any]], payload["error"]["details"][key])


@pytest.mark.parametrize("source_format", ["markdown", "asciidoc"])
def test_authored_section_prose_satisfies_strict_completeness(
    tmp_path: Path,
    source_format: str,
) -> None:
    init_project(tmp_path, source_format)
    _author_section_prose(tmp_path)
    exit_code, payload = _check_payload(tmp_path, strict=True)
    assert exit_code == 0, payload
    assert payload["result"]["errors"] == []
    assert payload["result"]["warnings"] == []


def test_placeholder_sections_warn_with_existing_markdown_paths(tmp_path: Path) -> None:
    init_project(tmp_path, "markdown")
    exit_code, payload = _check_payload(tmp_path, strict=True)
    assert exit_code == 1
    warnings = _findings(payload, "warnings")
    completeness = [
        finding
        for finding in warnings
        if "no authored section prose" in finding["message"]
    ]
    assert len(completeness) == 12
    assert all(finding["path"].endswith(".md") for finding in completeness)
    assert all(Path(finding["path"]).is_file() for finding in completeness)


def test_child_record_satisfies_empty_section(tmp_path: Path) -> None:
    init_project(tmp_path, "markdown")
    _author_section_prose(tmp_path, except_section="runtime_view")
    created = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "new", "runtime", "Runtime behavior"]
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, body = read_front_matter_document(record_path)
    metadata["status"] = "accepted"
    write_front_matter_document(record_path, metadata, body)
    exit_code, payload = _check_payload(tmp_path)
    assert exit_code == 0, payload
    warnings = _findings(payload, "warnings")
    assert not any(
        finding["message"].startswith("Section runtime_view has ")
        for finding in warnings
    )


@pytest.mark.parametrize("record_kind", ["section", "child"])
def test_draft_records_do_not_satisfy_completeness(
    tmp_path: Path,
    record_kind: str,
) -> None:
    init_project(tmp_path, "markdown")
    if record_kind == "section":
        _author_section_prose(tmp_path)
        paths, config, path_warnings = resolve_project_paths(tmp_path)
        assert not path_warnings
        section = next(paths.sections_dir.glob(f"*{config.section_extension}"))
        metadata, body = read_front_matter_document(section)
        metadata["status"] = "draft"
        write_front_matter_document(section, metadata, body)
    else:
        _author_section_prose(tmp_path, except_section="runtime_view")
        created = runner.invoke(
            app, ["--root", str(tmp_path), "--json", "new", "runtime", "Draft behavior"]
        )
        assert created.exit_code == 0, created.stdout
        record_path = Path(json.loads(created.stdout)["result"]["path"])
        metadata, body = read_front_matter_document(record_path)
        metadata["status"] = "draft"
        write_front_matter_document(record_path, metadata, body)
    exit_code, payload = _check_payload(tmp_path, strict=True)
    assert exit_code == 1
    warnings = _findings(payload, "warnings")
    assert any(
        "no authored section prose" in finding["message"] for finding in warnings
    )
    assert any("Draft record" in finding["message"] for finding in warnings)


def test_archived_child_record_does_not_satisfy_completeness(tmp_path: Path) -> None:
    init_project(tmp_path, "markdown")
    _author_section_prose(tmp_path, except_section="runtime_view")
    created = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "new", "runtime", "Archived behavior"]
    )
    assert created.exit_code == 0, created.stdout
    record_id = json.loads(created.stdout)["result"]["id"]
    archived = runner.invoke(
        app, ["--root", str(tmp_path), "archive", record_id, "--reason", "test"]
    )
    assert archived.exit_code == 0, archived.stdout
    exit_code, payload = _check_payload(tmp_path, strict=True)
    assert exit_code == 1
    warnings = _findings(payload, "warnings")
    assert any(
        finding["message"].startswith("Section runtime_view has ")
        for finding in warnings
    )


def test_missing_section_uses_configured_extension(tmp_path: Path) -> None:
    init_project(tmp_path, "markdown")
    paths, config, warnings = resolve_project_paths(tmp_path)
    assert not warnings
    missing = paths.sections_dir / f"content-0002{config.section_extension}"
    missing.unlink()
    exit_code, payload = _check_payload(tmp_path)
    assert exit_code == 1
    errors = _findings(payload, "errors")
    missing_finding = next(
        finding
        for finding in errors
        if "architecture_constraints" in finding["message"]
    )
    assert missing_finding["path"].endswith(config.section_extension)
    assert missing_finding["path"].endswith("content-0002.md")
