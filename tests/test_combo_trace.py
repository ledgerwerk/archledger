from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.combo_trace import build_combo_trace
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)

runner = CliRunner()


def test_combo_trace_empty_arrays_for_missing_fields() -> None:
    payload = build_combo_trace(
        {
            "schema": "archledger.trace.v1",
            "root": {"id": "al_runtime_0123", "status": "accepted"},
        }
    )

    assert payload["schema"] == "combi.trace.v1"
    assert payload["producer"] == "archledger"
    assert payload["subject"] == {"type": "archledger_record", "id": "al_runtime_0123"}
    assert payload["task_ids"] == []
    assert payload["ac_ids"] == []
    assert payload["bdd_ids"] == []
    assert payload["source_refs"] == []
    assert payload["test_refs"] == []
    assert payload["evidence_refs"] == []
    assert payload["gaps"] == []


def test_combo_trace_extracts_refs_from_trace_payload() -> None:
    payload = build_combo_trace(
        {
            "schema": "archledger.trace.v1",
            "root": {
                "id": "al_runtime_0123",
                "status": "accepted",
                "metadata": {
                    "task_id": "task-0037",
                    "acceptance_criteria": ["ac-0001"],
                    "bdd": {"id": "bdd-0002", "scenario_id": "bdd-0003"},
                    "related": ["al_requirement_0004"],
                },
            },
            "source_refs": [
                {"path": "specs/behavior/features/a/b.feature", "role": "documents"}
            ],
            "test_refs": [{"path": "tests/test_a.py", "nodeid": "test_b"}],
        }
    )

    assert payload["task_ids"] == ["task-0037"]
    assert payload["ac_ids"] == ["ac-0001"]
    assert payload["bdd_ids"] == ["bdd-0002", "bdd-0003"]
    assert payload["archledger_refs"] == ["al_requirement_0004"]
    assert payload["source_refs"] == [
        {"path": "specs/behavior/features/a/b.feature", "role": "documents"}
    ]
    assert payload["test_refs"] == [{"path": "tests/test_a.py", "nodeid": "test_b"}]


def test_trace_cli_combo_json_preserves_default_human_output(tmp_path: Path) -> None:
    init = runner.invoke(app, ["--root", str(tmp_path), "init", "--profile", "sdd"])
    assert init.exit_code == 0, init.stdout
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "runtime",
            "Checkout",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    result = json.loads(created.stdout)["result"]
    record_path = Path(result["path"])
    feature_path = tmp_path / "specs/behavior/features/checkout/pay.feature"
    feature_path.parent.mkdir(parents=True)
    feature_path.write_text("Feature: Checkout\n", encoding="utf-8")
    test_path = tmp_path / "tests/test_checkout.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_pay():\n    assert True\n", encoding="utf-8")
    metadata, body = read_front_matter_document(record_path)
    metadata["source_refs"] = [
        {"path": "specs/behavior/features/checkout/pay.feature", "role": "documents"}
    ]
    metadata["test_refs"] = ["tests/test_checkout.py::test_pay"]
    metadata["task_id"] = "task-0037"
    write_front_matter_document(record_path, metadata, body)

    default = runner.invoke(app, ["--root", str(tmp_path), "trace", result["id"]])
    assert default.exit_code == 0, default.stdout
    assert default.stdout.startswith(f"Trace for {result['id']}:")

    combo = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "trace",
            result["id"],
            "--format",
            "combo-json",
        ],
    )
    assert combo.exit_code == 0, combo.stdout
    payload = json.loads(combo.stdout)["result"]
    assert payload["schema"] == "combi.trace.v1"
    assert payload["task_ids"] == ["task-0037"]
    assert payload["source_refs"] == [
        {
            "path": "specs/behavior/features/checkout/pay.feature",
            "symbols": [],
            "role": "documents",
        }
    ]
    assert payload["test_refs"] == [
        {"path": "tests/test_checkout.py", "nodeid": "test_pay", "role": "validates"}
    ]
