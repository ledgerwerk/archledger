from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def init_project(tmp_path: Path, *, source_format: str = "asciidoc") -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", source_format],
    )
    assert result.exit_code == 0, result.stdout


def test_renumber_dry_run_does_not_mutate(tmp_path: Path) -> None:
    init_project(tmp_path)
    create = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "requirement", "A"],
    )
    assert create.exit_code == 0
    old_path = tmp_path / ".archledger" / "records" / "requirements" / "al_0013.adoc"

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "renumber",
            "--prefix",
            "ta",
            "--width",
            "3",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result"]["apply"] is False
    assert payload["result"]["renamed_count"] == 13
    assert old_path.is_file()
    assert not (
        tmp_path / ".archledger" / "records" / "requirements" / "ta_013.adoc"
    ).exists()


def test_renumber_apply_renames_files_updates_frontmatter_and_config(
    tmp_path: Path,
) -> None:
    init_project(tmp_path)
    parent_result = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "white-box", "Parent"],
    )
    assert parent_result.exit_code == 0
    child_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "white-box",
            "Child",
            "--parent",
            "al_0013",
        ],
    )
    assert child_result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "renumber",
            "--prefix",
            "ta",
            "--width",
            "3",
            "--apply",
        ],
    )

    assert result.exit_code == 0
    assert not (
        tmp_path / ".archledger" / "records" / "building_blocks" / "al_0013.adoc"
    ).exists()
    child = tmp_path / ".archledger" / "records" / "building_blocks" / "ta_014.adoc"
    assert child.is_file()
    child_text = child.read_text(encoding="utf-8")
    assert "id: ta_014" in child_text
    assert "parent: ta_013" in child_text
    assert "al_0013" not in child_text

    config_text = (tmp_path / "archledger.toml").read_text(encoding="utf-8")
    assert "[ids]" in config_text
    assert 'prefix = "ta"' in config_text
    assert "width = 3" in config_text

    check = runner.invoke(app, ["--root", str(tmp_path), "check"])
    assert check.exit_code == 0


def test_renumber_can_enable_content_segments_without_changing_numbers(
    tmp_path: Path,
) -> None:
    init_project(tmp_path, source_format="markdown")

    req = runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])
    assert req.exit_code == 0
    risk = runner.invoke(app, ["--root", str(tmp_path), "new", "risk", "B"])
    assert risk.exit_code == 0

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "renumber",
            "--id-segment-mode",
            "type",
            "--apply",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)

    renamed = {item["old_id"]: item["new_id"] for item in payload["result"]["renamed"]}
    assert renamed["al_0004"] == "al_content_0004"
    assert renamed["al_0013"] == "al_content_0013"
    assert renamed["al_0014"] == "al_risk_0014"

    assert (
        tmp_path
        / ".archledger"
        / "profiles"
        / "arc42"
        / "sections"
        / "al_content_0004.md"
    ).is_file()
    assert (
        tmp_path / ".archledger" / "records" / "requirements" / "al_content_0013.md"
    ).is_file()
    assert (
        tmp_path / ".archledger" / "records" / "risks" / "al_risk_0014.md"
    ).is_file()

    check = runner.invoke(app, ["--root", str(tmp_path), "check"])
    assert check.exit_code == 0, check.stdout


def test_renumber_can_disable_content_segments(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    create = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "risk", "A"],
    )
    assert create.exit_code == 0
    enable = runner.invoke(
        app,
        ["--root", str(tmp_path), "renumber", "--id-segment-mode", "type", "--apply"],
    )
    assert enable.exit_code == 0, enable.stdout

    disable = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "renumber",
            "--id-segment-mode",
            "none",
            "--apply",
        ],
    )
    assert disable.exit_code == 0, disable.stdout
    assert (tmp_path / ".archledger" / "records" / "risks" / "al_0013.md").is_file()


def test_renumber_segments_rewrite_parent_references(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    parent = runner.invoke(app, ["--root", str(tmp_path), "new", "white-box", "Parent"])
    assert parent.exit_code == 0
    child = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "new",
            "white-box",
            "Child",
            "--parent",
            "al_0013",
        ],
    )
    assert child.exit_code == 0

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "renumber",
            "--id-segment-mode",
            "type",
            "--apply",
        ],
    )
    assert result.exit_code == 0, result.output

    child_path = (
        tmp_path / ".archledger" / "records" / "building_blocks" / "al_block_0014.md"
    )
    assert child_path.is_file()
    child_text = child_path.read_text(encoding="utf-8")
    assert "parent: al_block_0013" in child_text
    assert "parent: al_0013" not in child_text


def test_renumber_apply_includes_archive_tombstones(tmp_path: Path) -> None:
    init_project(tmp_path)
    create = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "requirement", "A"],
    )
    assert create.exit_code == 0
    missing = tmp_path / ".archledger" / "records" / "requirements" / "al_0013.adoc"
    missing.unlink()
    repair = runner.invoke(app, ["--root", str(tmp_path), "doctor", "--repair"])
    assert repair.exit_code == 0, repair.output

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "renumber",
            "--prefix",
            "ta",
            "--width",
            "3",
            "--apply",
        ],
    )

    assert result.exit_code == 0
    assert (
        tmp_path / ".archledger" / "archive" / "tombstones" / "ta_013.adoc"
    ).is_file()
    assert not (
        tmp_path / ".archledger" / "archive" / "tombstones" / "al_0013.adoc"
    ).exists()


def test_renumber_segments_include_archive_tombstones(tmp_path: Path) -> None:
    init_project(tmp_path)
    create = runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "requirement", "A"],
    )
    assert create.exit_code == 0
    missing = tmp_path / ".archledger" / "records" / "requirements" / "al_0013.adoc"
    missing.unlink()
    repair = runner.invoke(app, ["--root", str(tmp_path), "doctor", "--repair"])
    assert repair.exit_code == 0, repair.output

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "renumber",
            "--id-segment-mode",
            "type",
            "--apply",
        ],
    )

    assert result.exit_code == 0
    assert (
        tmp_path / ".archledger" / "archive" / "tombstones" / "al_archive_0013.adoc"
    ).is_file()


def test_renumber_rejects_invalid_prefix(tmp_path: Path) -> None:
    init_project(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "renumber", "--prefix", "TA", "--width", "3"],
    )
    assert result.exit_code == 1
    assert "prefix" in result.output.lower()


def test_renumber_rejects_existing_target_file(tmp_path: Path) -> None:
    init_project(tmp_path)
    target = (
        tmp_path / ".archledger" / "profiles" / "arc42" / "sections" / "ta_001.adoc"
    )
    target.write_text("do not overwrite\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "renumber",
            "--prefix",
            "ta",
            "--width",
            "3",
            "--apply",
        ],
    )

    assert result.exit_code == 1
    assert target.read_text(encoding="utf-8") == "do not overwrite\n"
    assert target.read_text(encoding="utf-8") == "do not overwrite\n"


def test_renumber_from_flat_to_type_after_config_already_changed(
    tmp_path: Path,
) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])
    runner.invoke(app, ["--root", str(tmp_path), "new", "risk", "B"])

    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'segment_mode = "none"',
            'segment_mode = "type"',
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "renumber",
            "--from-id-segment-mode",
            "none",
            "--id-segment-mode",
            "type",
            "--apply",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (
        tmp_path / ".archledger" / "records" / "requirements" / "al_content_0013.md"
    ).is_file()
    assert (
        tmp_path / ".archledger" / "records" / "risks" / "al_risk_0014.md"
    ).is_file()
    assert not (
        tmp_path / ".archledger" / "records" / "requirements" / "al_0013.md"
    ).exists()

    check = runner.invoke(app, ["--root", str(tmp_path), "check"])
    assert check.exit_code == 0, check.stdout


def test_renumber_refuses_stale_generated_tombstone_collision_without_explicit_prune(
    tmp_path: Path,
) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])

    # Simulate bad prior repair after config was changed to type.
    tombstone_dir = tmp_path / ".archledger" / "archive" / "tombstones"
    tombstone_dir.mkdir(parents=True, exist_ok=True)
    (tombstone_dir / "al_archive_0013.md").write_text(
        "---\n"
        "schema_version: 2\n"
        "id: al_archive_0013\n"
        "type: archive_tombstone\n"
        "title: Archived placeholder for missing ledger ID al_archive_0013\n"
        "status: archived\n"
        "section: risks_and_technical_debt\n"
        "order: 13\n"
        'date: "2026-06-08"\n'
        "body_format: markdown\n"
        'created_at: "2026-06-08T00:00:00Z"\n'
        'updated_at: "2026-06-08T00:00:00Z"\n'
        'archived_at: "2026-06-08T00:00:00Z"\n'
        "archived_reason: Created by archledger doctor "
        "--repair for a missing ledger number.\n"
        "---\n\n"
        "This tombstone preserves a ledger number whose "
        "original source fragment is no longer present. "
        "It was created automatically by "
        "`archledger doctor --repair`.\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "renumber",
            "--from-id-segment-mode",
            "none",
            "--id-segment-mode",
            "type",
            "--apply",
        ],
    )

    assert result.exit_code == 1
    assert "generated tombstone" in result.output.lower()
    assert "--prune-generated-tombstones" in result.output
    assert (tombstone_dir / "al_archive_0013.md").is_file()


def test_renumber_prune_generated_tombstones_moves_to_quarantine(
    tmp_path: Path,
) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])

    # Simulate bad prior repair after config was changed to type.
    tombstone_dir = tmp_path / ".archledger" / "archive" / "tombstones"
    tombstone_dir.mkdir(parents=True, exist_ok=True)
    (tombstone_dir / "al_archive_0013.md").write_text(
        "---\n"
        "schema_version: 2\n"
        "id: al_archive_0013\n"
        "type: archive_tombstone\n"
        "title: Archived placeholder for missing ledger ID al_archive_0013\n"
        "status: archived\n"
        "section: risks_and_technical_debt\n"
        "order: 13\n"
        'date: "2026-06-08"\n'
        "body_format: markdown\n"
        'created_at: "2026-06-08T00:00:00Z"\n'
        'updated_at: "2026-06-08T00:00:00Z"\n'
        'archived_at: "2026-06-08T00:00:00Z"\n'
        "archived_reason: Created by archledger doctor "
        "--repair for a missing ledger number.\n"
        "---\n\n"
        "This tombstone preserves a ledger number whose "
        "original source fragment is no longer present. "
        "It was created automatically by "
        "`archledger doctor --repair`.\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "renumber",
            "--from-id-segment-mode",
            "none",
            "--id-segment-mode",
            "type",
            "--prune-generated-tombstones",
            "--apply",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert not (tombstone_dir / "al_archive_0013.md").exists()
    payload = json.loads(result.stdout)
    quarantined = payload["result"].get("quarantined_generated_tombstones", [])
    assert len(quarantined) == 1
    qpath = Path(quarantined[0]["quarantine_path"])
    assert "archive" in qpath.parts
    assert "quarantine" in qpath.parts


def test_renumber_infers_hidden_flat_to_type(tmp_path: Path) -> None:
    init_project(tmp_path, source_format="markdown")
    runner.invoke(app, ["--root", str(tmp_path), "new", "requirement", "A"])
    runner.invoke(app, ["--root", str(tmp_path), "new", "risk", "B"])

    canonical_config = tmp_path / "archledger.toml"
    hidden_config = tmp_path / ".archledger.toml"
    hidden_config.write_text(
        canonical_config.read_text(encoding="utf-8").replace(
            'segment_mode = "none"',
            'segment_mode = "type"',
        ),
        encoding="utf-8",
    )
    canonical_config.unlink()

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "renumber",
            "--apply",
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["result"]["old_format"]["segment_mode"] == "none"
    assert payload["result"]["new_format"]["segment_mode"] == "type"
    assert (
        tmp_path
        / ".archledger"
        / "profiles"
        / "arc42"
        / "sections"
        / "al_content_0001.md"
    ).is_file()
    assert (
        tmp_path / ".archledger" / "records" / "requirements" / "al_content_0013.md"
    ).is_file()
    assert (
        tmp_path / ".archledger" / "records" / "risks" / "al_risk_0014.md"
    ).is_file()
    assert not (
        tmp_path / ".archledger" / "records" / "requirements" / "al_0013.md"
    ).exists()
    assert not canonical_config.exists()
    assert hidden_config.exists()
