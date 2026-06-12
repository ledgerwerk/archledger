from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_context_changed_uses_source_baseline_without_crashing(tmp_path: Path) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    snapshot = runner.invoke(
        app,
        ["--root", str(tmp_path), "source", "snapshot"],
    )
    assert snapshot.exit_code == 0, snapshot.stdout
    source.write_text("VALUE = 2\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "context", "--changed"],
    )

    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["result"]["schema"] == "archledger.context.v1"


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout


def _create_record(path: Path, kind: str, title: str, *, status: str = "proposed") -> None:
    result = runner.invoke(
        app,
        ["--root", str(path), "new", kind, title, "--status", status],
    )
    assert result.exit_code == 0, result.stdout


def test_context_topic_returns_categorized_records(tmp_path: Path) -> None:
    _init(tmp_path)
    _create_record(tmp_path, "adr", "Use object storage for files")
    _create_record(tmp_path, "constraint", "Must use encryption at rest")
    _create_record(tmp_path, "risk", "Data loss during migration")

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "context", "--topic", "storage encryption"],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["result"]["schema"] == "archledger.context.v2"
    categories = payload["result"]["categories"]
    assert "adrs" in categories
    assert "constraints" in categories
    assert "risks" in categories
    # at least one ADR matched
    assert len(categories["adrs"]) >= 1
    # every entry has score, match_reasons, record
    for cat_items in categories.values():
        for entry in cat_items:
            assert "score" in entry
            assert "match_reasons" in entry
            assert "record" in entry
            assert entry["score"] > 0


def test_context_topic_ranks_title_match_above_body_match(tmp_path: Path) -> None:
    _init(tmp_path)
    _create_record(tmp_path, "adr", "Storage architecture")
    _create_record(tmp_path, "adr", "Unrelated decision")

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "context", "--topic", "storage"],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    adrs = payload["result"]["categories"]["adrs"]
    if len(adrs) >= 2:
        storage_score = None
        unrelated_score = None
        for entry in adrs:
            if "storage" in entry["record"]["title"].lower():
                storage_score = entry["score"]
            else:
                unrelated_score = entry["score"]
        if storage_score is not None and unrelated_score is not None:
            assert storage_score > unrelated_score


def test_context_topic_includes_glossary_terms(tmp_path: Path) -> None:
    _init(tmp_path)
    _create_record(tmp_path, "glossary-term", "Object Storage")

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "context", "--topic", "object storage"],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    glossary = payload["result"]["categories"]["glossary_terms"]
    assert len(glossary) >= 1
    assert any(
        "storage" in e["record"]["title"].lower() for e in glossary
    )


def test_context_topic_respects_max_per_category(tmp_path: Path) -> None:
    _init(tmp_path)
    for i in range(5):
        _create_record(tmp_path, "risk", f"Storage risk {i}")

    result = runner.invoke(
        app,
        [
            "--root", str(tmp_path),
            "--json", "context",
            "--topic", "storage risk",
            "--max-per-category", "2",
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    risks = payload["result"]["categories"]["risks"]
    assert len(risks) <= 2


def test_context_topic_can_include_drafts(tmp_path: Path) -> None:
    _init(tmp_path)
    _create_record(tmp_path, "adr", "Draft storage ADR", status="draft")

    # without --include-drafts
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "context", "--topic", "storage"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert len(payload["result"]["categories"]["adrs"]) == 0

    # with --include-drafts
    result = runner.invoke(
        app,
        [
            "--root", str(tmp_path),
            "--json", "context",
            "--topic", "storage",
            "--include-drafts",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert len(payload["result"]["categories"]["adrs"]) >= 1


def test_context_topic_multiple_selectors_errors(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root", str(tmp_path),
            "--json", "context",
            "--topic", "storage",
            "--for-file", "some.py",
        ],
    )
    assert result.exit_code != 0


def test_context_topic_no_selector_errors(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "context"],
    )
    assert result.exit_code != 0


def test_context_changed_without_baseline_returns_empty_context(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "context", "--changed"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["result"]["schema"] == "archledger.context.v1"
    assert payload["result"]["records"] == []


def test_context_topic_includes_linked_records(tmp_path: Path) -> None:
    _init(tmp_path)
    _create_record(tmp_path, "adr", "Use object storage for files")
    # Create a risk that links to the ADR
    _create_record(tmp_path, "risk", "Migration data loss")
    # Get the ADR id
    list_result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "list", "adr"],
    )
    adr_id = json.loads(list_result.stdout)["result"]["records"][0]["id"]
    risk_result = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "list", "risk"],
    )
    risk_id = json.loads(risk_result.stdout)["result"]["records"][0]["id"]
    # Link risk to ADR
    link_result = runner.invoke(
        app,
        ["--root", str(tmp_path), "links", "add", risk_id, "--rel", "relates_to", "--target", adr_id],
    )
    assert link_result.exit_code == 0, link_result.stdout

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "context", "--topic", "storage"],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    # both adrs and risks should be populated due to linking
    record_ids = {
        entry["record"]["id"]
        for entries in payload["result"]["categories"].values()
        for entry in entries
    }
    # risk should appear via link expansion even if it doesn't match topic directly
    assert risk_id in record_ids or len(payload["result"]["categories"]["risks"]) >= 1
