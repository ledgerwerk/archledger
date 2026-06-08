"""Tests for archledger.bdd.inspect — direct unit tests.

Covers list_bdd_records, bdd_status_summary, and status_entry_dicts
beyond what the CLI integration tests exercise.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from archledger.bdd.inspect import (
    bdd_status_summary,
    list_bdd_records,
    status_entry_dicts,
)
from archledger.repository import ArchitectureRepository
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)


@pytest.fixture()
def _repo(tmp_path: Path) -> ArchitectureRepository:
    from typer.testing import CliRunner

    from archledger.cli import app
    from archledger.storage.paths import resolve_project_paths

    runner = CliRunner()
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert result.exit_code == 0, result.stdout
    paths, config, _ = resolve_project_paths(tmp_path)
    return ArchitectureRepository(paths, config)


def _make_record(
    repo: ArchitectureRepository,
    *,
    title: str = "S",
    bdd: dict | None = None,
) -> str:
    record = repo.create_record("runtime_scenario", title, status="accepted")
    if bdd is not None:
        fm, body = read_front_matter_document(record.path)
        fm["bdd"] = bdd
        write_front_matter_document(record.path, fm, body)
    return record.id


class TestListBddRecords:
    """@bdd-list-all-records, @bdd-list-filter-automation, @bdd-list-invalid-metadata"""

    def test_returns_only_bdd_records(self, _repo: ArchitectureRepository) -> None:
        _make_record(_repo, title="With", bdd={"feature": "F", "scenario": "S"})
        _make_record(_repo, title="Without")  # no bdd metadata

        resp = list_bdd_records(_repo)
        assert resp.count == 1
        assert resp.entries[0].record_id is not None

    def test_automation_filter(self, _repo: ArchitectureRepository) -> None:
        _make_record(
            _repo,
            title="Automated",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "automated", "command": "pytest"},
            },
        )
        _make_record(
            _repo,
            title="Pending",
            bdd={
                "feature": "F",
                "scenario": "S2",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "pending"},
            },
        )

        resp = list_bdd_records(_repo, automation_filter="automated")
        assert resp.count == 1
        assert resp.entries[0].automation_status == "automated"

    def test_status_filter(self, _repo: ArchitectureRepository) -> None:
        _make_record(
            _repo,
            title="Accepted",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
            },
        )

        resp = list_bdd_records(_repo, status_filter="accepted")
        assert resp.count == 1
        resp2 = list_bdd_records(_repo, status_filter="proposed")
        assert resp2.count == 0

    def test_feature_filter(self, _repo: ArchitectureRepository) -> None:
        _make_record(
            _repo,
            title="A",
            bdd={
                "feature": "Task lifecycle",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
            },
        )
        _make_record(
            _repo,
            title="B",
            bdd={
                "feature": "Other",
                "scenario": "S2",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
            },
        )

        resp = list_bdd_records(_repo, feature_filter="Task lifecycle")
        assert resp.count == 1
        assert resp.entries[0].feature == "Task lifecycle"

    def test_invalid_metadata_entry(self, _repo: ArchitectureRepository) -> None:
        _make_record(
            _repo,
            title="Bad",
            bdd="not-a-mapping",
        )

        resp = list_bdd_records(_repo)
        assert resp.count == 1
        assert resp.entries[0].valid is False

    def test_schema_field(self, _repo: ArchitectureRepository) -> None:
        resp = list_bdd_records(_repo)
        assert resp.schema == "archledger.bdd-list.v1"

    def test_command_present_flag(self, _repo: ArchitectureRepository) -> None:
        _make_record(
            _repo,
            title="WithCommand",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "automated", "command": "pytest -q"},
            },
        )
        _make_record(
            _repo,
            title="NoCommand",
            bdd={
                "feature": "F",
                "scenario": "S2",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "pending"},
            },
        )

        resp = list_bdd_records(_repo)
        entries = {e.scenario: e for e in resp.entries}
        assert entries["S"].command_present is True
        assert entries["S2"].command_present is False


class TestBddStatusSummary:
    """@bdd-status-totals, @bdd-status-coverage"""

    def test_empty_project(self, _repo: ArchitectureRepository) -> None:
        resp = bdd_status_summary(_repo)
        assert resp.totals["examples"] == 0
        assert resp.totals["invalid_metadata"] == 0

    def test_counts_valid_and_invalid(self, _repo: ArchitectureRepository) -> None:
        _make_record(
            _repo,
            title="Good",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "linked", "feature_file": "f.feature"},
            },
        )
        _make_record(_repo, title="Bad", bdd="not-a-mapping")

        resp = bdd_status_summary(_repo)
        assert resp.totals["examples"] == 2
        assert resp.totals["invalid_metadata"] == 1

    def test_coverage_dimensions(self, _repo: ArchitectureRepository) -> None:
        _make_record(
            _repo,
            title="A",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "linked", "feature_file": "f.feature"},
            },
        )
        _make_record(
            _repo,
            title="B",
            bdd={
                "feature": "F",
                "scenario": "S2",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "pending"},
            },
        )

        resp = bdd_status_summary(_repo)
        assert resp.totals["examples"] == 2
        assert resp.coverage["complete_gwt"] == {"covered": 2, "total": 2}
        assert resp.coverage["linked_feature_files"] == {"covered": 1, "total": 2}
        assert resp.coverage["automated"] == {"covered": 0, "total": 2}
        assert resp.coverage["pending"] == {"covered": 1, "total": 2}

    def test_schema_field(self, _repo: ArchitectureRepository) -> None:
        resp = bdd_status_summary(_repo)
        assert resp.schema == "archledger.bdd-status.v1"

    def test_incomplete_gwt_not_counted_as_complete(
        self, _repo: ArchitectureRepository
    ) -> None:
        _make_record(
            _repo,
            title="Incomplete",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": [],
                "when": ["w"],
                "then": ["t"],
            },
        )
        resp = bdd_status_summary(_repo)
        assert resp.totals["examples"] == 1
        assert resp.coverage["complete_gwt"] == {"covered": 0, "total": 1}


class TestStatusEntryDicts:
    """Covers the status_entry_dicts helper."""

    def test_converts_entries_to_dicts(self, _repo: ArchitectureRepository) -> None:
        _make_record(
            _repo,
            title="S",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
            },
        )
        resp = list_bdd_records(_repo)
        dicts = status_entry_dicts(resp)
        assert len(dicts) == 1
        assert dicts[0]["feature"] == "F"
        assert dicts[0]["scenario"] == "S"
        assert isinstance(dicts[0]["valid"], bool)

    def test_empty_response(self, _repo: ArchitectureRepository) -> None:
        resp = list_bdd_records(_repo)
        dicts = status_entry_dicts(resp)
        assert dicts == []
