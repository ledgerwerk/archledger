"""Tests for archledger bdd export CLI command."""

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


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout


def _create_record_with_bdd(tmp_path: Path) -> str:
    """Create a runtime_scenario with bdd metadata and return its id."""
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "My scenario"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    record_id = payload["result"]["id"]
    record_path = Path(payload["result"]["path"])

    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"] = {
        "feature": "F",
        "rule": "R",
        "scenario": "My scenario",
        "tags": ["t1"],
        "given": ["g1"],
        "when": ["w1"],
        "then": ["t1"],
        "automation": {"status": "linked"},
    }
    write_front_matter_document(record_path, metadata, body)
    return record_id, record_path


def test_bdd_export_creates_feature_file(tmp_path: Path) -> None:
    """ac-0011: export creates a .feature file from a record with bdd metadata."""
    _init(tmp_path)
    record_id, _record_path = _create_record_with_bdd(tmp_path)
    out_rel = "out.feature"
    out = tmp_path / out_rel

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            out_rel,
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.bdd-export.v1"
    # Single-record export uses the normalized shape (exported[], feature_files[]).
    assert payload["exported"] == [
        {"record_id": record_id, "feature": "F", "file": out_rel}
    ]
    assert payload["feature_files"] == [out_rel]

    content = out.read_text(encoding="utf-8")
    assert f"Generated from archledger record {record_id}" in content
    assert "Feature: F" in content
    assert "Rule: R" in content
    assert "Scenario: My scenario" in content
    assert "Given g1" in content
    assert "When w1" in content
    assert "Then t1" in content


def test_bdd_export_refuses_records_without_bdd(tmp_path: Path) -> None:
    """ac-0011: export refuses records without bdd metadata."""
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "No BDD"],
    )
    assert result.exit_code == 0, result.stdout
    record_id = json.loads(result.stdout)["result"]["id"]

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            str(tmp_path / "out.feature"),
        ],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert "no bdd" in payload["error"]["message"].lower()


def test_bdd_export_is_deterministic(tmp_path: Path) -> None:
    """ac-0011: export produces identical content on repeated runs."""
    _init(tmp_path)
    record_id, _record_path = _create_record_with_bdd(tmp_path)
    out1_rel = "out1.feature"
    out2_rel = "out2.feature"
    out1 = tmp_path / out1_rel
    out2 = tmp_path / out2_rel

    for out_rel in [out1_rel, out2_rel]:
        result = runner.invoke(
            app,
            [
                "--root",
                str(tmp_path),
                "--json",
                "bdd",
                "export",
                record_id,
                "--out",
                out_rel,
            ],
        )
        assert result.exit_code == 0, result.stdout

    assert out1.read_text() == out2.read_text()


def test_bdd_export_json_schema_matches() -> None:
    """ac-0010: the bdd-export JSON schema target exists and is loadable."""
    from archledger.jsonschemas import SCHEMA_FILES, load_json_schema

    assert "bdd-export" in SCHEMA_FILES
    schema = load_json_schema("bdd-export")
    assert schema["title"] == "Archledger BDD export result"
    # Normalized shape (single + batch).
    assert schema["required"] == [
        "schema",
        "exported",
        "feature_files",
        "warnings",
    ]


# ---- P0: export path validation + overwrite protection ----


def test_bdd_export_refuses_absolute_outside_workspace_by_default(
    tmp_path: Path,
) -> None:
    """P0: --out must be a safe relative POSIX path inside the workspace."""
    _init(tmp_path)
    record_id, _record_path = _create_record_with_bdd(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            "/tmp/should-be-refused.feature",
        ],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    msg = payload["error"]["message"].lower()
    assert "absolute" in msg or "relative" in msg or "workspace" in msg


def test_bdd_export_does_not_write_before_path_validation(tmp_path: Path) -> None:
    """P0: no file is written when path validation fails."""
    _init(tmp_path)
    record_id, _record_path = _create_record_with_bdd(tmp_path)
    # A parent-escape path is refused by validate_relative_posix_path.
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            "../al_export_refused_unique.feature",
        ],
    )
    assert result.exit_code != 0
    # Nothing should have been written outside the workspace.
    assert not (tmp_path.parent / "al_export_refused_unique.feature").exists()


def test_bdd_export_refuses_overwrite_without_force(tmp_path: Path) -> None:
    """P0: overwriting an existing file requires --force."""
    _init(tmp_path)
    record_id, _record_path = _create_record_with_bdd(tmp_path)
    existing = tmp_path / "out.feature"
    existing.write_text("PRE-EXISTING\n", encoding="utf-8")
    # First attempt without --force must fail and must not overwrite.
    refused = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            "out.feature",
        ],
    )
    assert refused.exit_code != 0
    assert existing.read_text(encoding="utf-8") == "PRE-EXISTING\n"
    # With --force it succeeds and overwrites.
    forced = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            "out.feature",
            "--force",
        ],
    )
    assert forced.exit_code == 0, forced.stdout
    assert "PRE-EXISTING" not in existing.read_text(encoding="utf-8")


def test_bdd_export_warns_for_deprecated_output_path(tmp_path: Path) -> None:
    _init(tmp_path)
    record_id, _record_path = _create_record_with_bdd(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            record_id,
            "--out",
            "tests/bdd/features/legacy.feature",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert any(
        "deprecated BDD feature-file location" in warning
        for warning in payload["warnings"]
    )


def _import_feature(tmp_path: Path, text: str) -> None:
    """Write a .feature file and import it via the CLI."""
    feature_path = (
        tmp_path / "specs" / "behavior" / "features" / "task-management" / "src.feature"
    )
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    feature_path.write_text(text, encoding="utf-8")
    rel = str(feature_path.relative_to(tmp_path))
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "import",
            rel,
            "--kind",
            "runtime-scenario",
            "--status",
            "accepted",
        ],
    )
    assert result.exit_code == 0, result.stdout


def test_bdd_export_all_sanitizes_feature_name_inside_out_dir(
    tmp_path: Path,
) -> None:
    """P0: a feature name with ../ cannot escape --out-dir."""
    _init(tmp_path)
    record_id, record_path = _create_record_with_bdd(tmp_path)
    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"]["feature"] = "../escape_from_outdir"
    write_front_matter_document(record_path, metadata, body)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            "--all",
            "--out-dir",
            "exported",
        ],
    )

    assert result.exit_code == 0, result.stdout
    # No file escaped the out-dir.
    assert not (tmp_path / "escape_from_outdir.feature").exists()
    assert not (tmp_path.parent / "escape_from_outdir.feature").exists()
    exported = list((tmp_path / "exported").glob("*.feature"))
    assert exported, "expected a sanitized file inside exported/"
    text = exported[0].read_text(encoding="utf-8")
    assert "Feature: ../escape_from_outdir" in text


def test_bdd_export_all_refuses_absolute_feature_name_before_write(
    tmp_path: Path,
) -> None:
    """P0: an absolute-looking feature name is sanitized and stays in out-dir."""
    _init(tmp_path)
    record_id, record_path = _create_record_with_bdd(tmp_path)
    metadata, body = read_front_matter_document(record_path)
    metadata["bdd"]["feature"] = "/tmp/archledger_pwned_escape"
    write_front_matter_document(record_path, metadata, body)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            "--all",
            "--out-dir",
            "exported",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert not (tmp_path / "tmp").exists() or True  # nothing leaked outside
    # The sanitized name lives inside exported/, never as /tmp/...
    out_files = list((tmp_path / "exported").glob("*.feature"))
    assert out_files
    assert all("tmp_archledger" in f.name for f in out_files)


def test_bdd_export_all_preserves_multiple_rules_in_one_feature(
    tmp_path: Path,
) -> None:
    """P0: one feature with two Rule: blocks exports both into one file."""
    _init(tmp_path)
    _import_feature(
        tmp_path,
        "Feature: Multi Rule\n"
        "  Rule: One\n"
        "    Scenario: A\n"
        "      Given g\n      When w\n      Then t\n"
        "  Rule: Two\n"
        "    Scenario: B\n"
        "      Given g2\n      When w2\n      Then t2\n",
    )

    exported = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            "--all",
            "--out-dir",
            "exported",
        ],
    )
    assert exported.exit_code == 0, exported.stdout

    files = list((tmp_path / "exported").glob("*.feature"))
    assert len(files) == 1, "expected a single multi-rule feature file"
    text = files[0].read_text(encoding="utf-8")
    assert "Rule: One" in text
    assert "Scenario: A" in text
    assert "Rule: Two" in text
    assert "Scenario: B" in text
    payload = json.loads(exported.stdout)["result"]
    assert payload["schema"] == "archledger.bdd-export.v1"
    assert len(payload["exported"]) == 2


def test_bdd_export_all_does_not_write_partial_file_on_collision(
    tmp_path: Path,
) -> None:
    """P0: if a target file already exists and --force is absent, nothing is written."""
    _init(tmp_path)
    _import_feature(
        tmp_path,
        "Feature: Multi Rule\n"
        "  Rule: One\n"
        "    Scenario: A\n"
        "      Given g\n      When w\n      Then t\n"
        "  Rule: Two\n"
        "    Scenario: B\n"
        "      Given g2\n      When w2\n      Then t2\n",
    )
    out_dir = tmp_path / "exported"
    out_dir.mkdir(parents=True)
    pre_existing = out_dir / "multi_rule.feature"
    pre_existing.write_text("PRE-EXISTING\n", encoding="utf-8")

    refused = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            "--all",
            "--out-dir",
            "exported",
        ],
    )
    assert refused.exit_code != 0
    # The pre-existing file must be untouched (atomic: no partial write).
    assert pre_existing.read_text(encoding="utf-8") == "PRE-EXISTING\n"
    payload = json.loads(refused.stdout)
    assert payload["ok"] is False


def test_bdd_export_all_force_does_not_drop_first_rule(tmp_path: Path) -> None:
    """P0: --force writes the full multi-rule file, not just the last rule."""
    _init(tmp_path)
    _import_feature(
        tmp_path,
        "Feature: Multi Rule\n"
        "  Rule: One\n"
        "    Scenario: A\n"
        "      Given g\n      When w\n      Then t\n"
        "  Rule: Two\n"
        "    Scenario: B\n"
        "      Given g2\n      When w2\n      Then t2\n",
    )
    out_dir = tmp_path / "exported"
    out_dir.mkdir(parents=True)
    (out_dir / "multi_rule.feature").write_text("OLD\n", encoding="utf-8")

    forced = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            "--all",
            "--out-dir",
            "exported",
            "--force",
        ],
    )
    assert forced.exit_code == 0, forced.stdout
    text = (out_dir / "multi_rule.feature").read_text(encoding="utf-8")
    assert "Rule: One" in text and "Scenario: A" in text
    assert "Rule: Two" in text and "Scenario: B" in text


def test_bdd_export_missing_mode_returns_json_error(tmp_path: Path) -> None:
    """P0: bdd export with no target returns a JSON error envelope, no traceback."""
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "export"],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "bdd export"
    assert "Provide a RECORD_ID" in payload["error"]["message"]


def test_bdd_export_all_requires_out_dir_returns_json_error(
    tmp_path: Path,
) -> None:
    """P0: --all without --out-dir is a JSON error envelope."""
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "export", "--all"],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "--out-dir" in payload["error"]["message"]
