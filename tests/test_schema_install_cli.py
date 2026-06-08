from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_schema_jsonschema_target_is_returned(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "schema",
            "--format",
            "jsonschema",
            "--target",
            "record",
        ],
    )

    assert result.exit_code == 0, result.stdout
    schema = json.loads(result.stdout)["result"]
    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["title"] == "Archledger record front matter"


def test_install_refuses_overwrite_without_force(tmp_path: Path) -> None:
    _init(tmp_path)
    first = runner.invoke(
        app,
        ["--root", str(tmp_path), "install", "pr-template"],
    )
    second = runner.invoke(
        app,
        ["--root", str(tmp_path), "install", "pr-template"],
    )
    forced = runner.invoke(
        app,
        ["--root", str(tmp_path), "install", "pr-template", "--force"],
    )

    assert first.exit_code == 0, first.stdout
    assert second.exit_code == 1
    assert "Refusing to overwrite" in second.stderr
    assert forced.exit_code == 0, forced.stdout


def _payload_matches_schema(payload: dict, schema: dict) -> None:
    """Lightweight structural check: required keys present and schema const matches.

    This catches schema drift without requiring the ``jsonschema`` runtime, by
    asserting the emitted payload exposes every key the published schema
    marks ``required`` and that the ``schema`` const matches the payload.
    """
    required = set(schema.get("required", []))
    missing = required - set(payload.keys())
    assert not missing, f"payload missing required keys {sorted(missing)}"
    schema_const = schema.get("properties", {}).get("schema", {}).get("const")
    if schema_const is not None:
        assert payload["schema"] == schema_const


def test_sdd_check_v2_payload_matches_schema(tmp_path: Path) -> None:
    """ac-0009: sdd check emits v2 fields that satisfy the published schema."""
    from archledger.jsonschemas import load_json_schema

    init_result = runner.invoke(
        app, ["--root", str(tmp_path), "init", "--profile", "sdd"]
    )
    assert init_result.exit_code == 0, init_result.stdout
    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )
    assert checked.exit_code == 0, checked.stdout
    payload = json.loads(checked.stdout)["result"]
    schema = load_json_schema("sdd-check")
    _payload_matches_schema(payload, schema)
    assert "profile" not in payload and "profile_enabled" not in payload


def test_bdd_export_payload_matches_schema(tmp_path: Path) -> None:
    """ac-0004: single and batch export payloads match the v1 schema."""
    from archledger.jsonschemas import load_json_schema
    from archledger.storage.frontmatter import (
        read_front_matter_document,
        write_front_matter_document,
    )

    _init(tmp_path)
    schema = load_json_schema("bdd-export")

    # Single-record export.
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime_scenario", "S"],
    )
    assert created.exit_code == 0, created.stdout
    rid = json.loads(created.stdout)["result"]["id"]
    rpath = Path(json.loads(created.stdout)["result"]["path"])
    metadata, body = read_front_matter_document(rpath)
    metadata["bdd"] = {
        "feature": "F",
        "rule": "R",
        "scenario": "S",
        "given": ["g"],
        "when": ["w"],
        "then": ["t"],
    }
    write_front_matter_document(rpath, metadata, body)
    single = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "export",
            rid,
            "--out",
            "out.feature",
        ],
    )
    assert single.exit_code == 0, single.stdout
    single_payload = json.loads(single.stdout)["result"]
    _payload_matches_schema(single_payload, schema)

    # Batch export.
    batch = runner.invoke(
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
    assert batch.exit_code == 0, batch.stdout
    batch_payload = json.loads(batch.stdout)["result"]
    _payload_matches_schema(batch_payload, schema)


def test_bdd_sync_payload_matches_schema(tmp_path: Path) -> None:
    """ac-0011: bdd sync payload matches the published schema."""
    from archledger.jsonschemas import load_json_schema

    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "sync", "--check"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    schema = load_json_schema("bdd-sync")
    _payload_matches_schema(payload, schema)


def test_sdd_init_payload_matches_schema(tmp_path: Path) -> None:
    """ac-0005: sdd init payload matches the published schema."""
    from archledger.jsonschemas import load_json_schema

    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "init", "--seed", "minimal"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    schema = load_json_schema("sdd-init")
    _payload_matches_schema(payload, schema)


def test_sdd_explain_payload_matches_schema(tmp_path: Path) -> None:
    """ac-0005: sdd explain (single + all) payload matches the schema."""
    from archledger.jsonschemas import load_json_schema

    _init(tmp_path)
    schema = load_json_schema("sdd-explain")
    single = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "explain", "SDD-BDD-GWT"],
    )
    assert single.exit_code == 0, single.stdout
    single_payload = json.loads(single.stdout)["result"]
    _payload_matches_schema(single_payload, schema)
    assert "rules" not in single_payload

    all_rules = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "explain", "--all"],
    )
    assert all_rules.exit_code == 0, all_rules.stdout
    all_payload = json.loads(all_rules.stdout)["result"]
    _payload_matches_schema(all_payload, schema)
    assert "rules" in all_payload and all_payload["rules"]


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout
