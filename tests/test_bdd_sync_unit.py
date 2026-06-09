"""Tests for archledger.bdd.sync — direct unit tests.

Covers check_bdd_sync beyond the CLI integration tests,
including invalid metadata detection and edge cases.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from archledger.bdd.sync import check_bdd_sync
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
    bdd: dict,
) -> str:
    record = repo.create_record("runtime_scenario", title, status="accepted")
    fm, body = read_front_matter_document(record.path)
    fm["bdd"] = bdd
    write_front_matter_document(record.path, fm, body)
    return record.id


def _write_feature(repo: ArchitectureRepository, rel_path: str, text: str) -> None:
    p = repo.paths.workspace_root / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class TestCheckBddSync:
    """Direct unit tests for sync drift detection."""

    def test_no_records_with_bdd(self, _repo: ArchitectureRepository) -> None:
        resp = check_bdd_sync(_repo)
        assert resp.checked == 0
        assert resp.findings == ()
        assert resp.feature_files_checked == 0

    def test_invalid_metadata_is_reported(self, _repo: ArchitectureRepository) -> None:
        _make_record(_repo, title="Bad", bdd="not-a-mapping")
        resp = check_bdd_sync(_repo)
        codes = [f.code for f in resp.findings]
        assert "BDD-SYNC-INVALID-METADATA" in codes

    def test_no_linked_file_is_not_an_error(
        self, _repo: ArchitectureRepository
    ) -> None:
        """Records with automation but no feature_file are simply skipped."""
        _make_record(
            _repo,
            title="Unlinked",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "pending"},
            },
        )
        resp = check_bdd_sync(_repo)
        assert resp.checked == 1
        # No FILE-MISSING because there is no linked file
        codes = [f.code for f in resp.findings]
        assert "BDD-SYNC-FILE-MISSING" not in codes

    def test_missing_linked_file(self, _repo: ArchitectureRepository) -> None:
        _make_record(
            _repo,
            title="Missing",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "nonexistent.feature",
                },
            },
        )
        resp = check_bdd_sync(_repo)
        codes = [f.code for f in resp.findings]
        assert "BDD-SYNC-FILE-MISSING" in codes
        assert resp.feature_files_checked >= 1

    def test_scenario_missing_from_feature(self, _repo: ArchitectureRepository) -> None:
        _write_feature(
            _repo,
            "specs/behavior/features/x.feature",
            "Feature: F\n  Scenario: Other\n    Given g\n    When w\n    Then t\n",
        )
        _make_record(
            _repo,
            title="Wrong",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "specs/behavior/features/x.feature",
                },
            },
        )
        resp = check_bdd_sync(_repo)
        codes = [f.code for f in resp.findings]
        assert "BDD-SYNC-SCENARIO-MISSING" in codes

    def test_gwt_mismatch(self, _repo: ArchitectureRepository) -> None:
        _write_feature(
            _repo,
            "specs/behavior/features/x.feature",
            "Feature: F\n  Scenario: S\n    Given different\n    When w\n    Then t\n",
        )
        _make_record(
            _repo,
            title="Drift",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "specs/behavior/features/x.feature",
                },
            },
        )
        resp = check_bdd_sync(_repo)
        codes = [f.code for f in resp.findings]
        assert "BDD-SYNC-GWT-MISMATCH" in codes

    def test_orphan_scenario(self, _repo: ArchitectureRepository) -> None:
        _write_feature(
            _repo,
            "specs/behavior/features/x.feature",
            (
                "Feature: F\n"
                "  Scenario: S\n    Given g\n    When w\n    Then t\n"
                "  Scenario: Orphan\n    Given x\n    When y\n    Then z\n"
            ),
        )
        _make_record(
            _repo,
            title="Match",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "specs/behavior/features/x.feature",
                },
            },
        )
        resp = check_bdd_sync(_repo)
        codes = [f.code for f in resp.findings]
        assert "BDD-SYNC-ORPHAN-SCENARIO" in codes

    def test_deprecated_path_warning(self, _repo: ArchitectureRepository) -> None:
        _write_feature(
            _repo,
            "tests/bdd/features/legacy.feature",
            "Feature: F\n  Scenario: S\n    Given g\n    When w\n    Then t\n",
        )
        _make_record(
            _repo,
            title="Legacy",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "tests/bdd/features/legacy.feature",
                },
            },
        )
        resp = check_bdd_sync(_repo)
        codes = [f.code for f in resp.findings]
        assert "BDD-FEATURE-PATH-CONVENTION" in codes

    def test_clean_sync(self, _repo: ArchitectureRepository) -> None:
        _write_feature(
            _repo,
            "specs/behavior/features/x.feature",
            "Feature: F\n  Scenario: S\n    Given g\n    When w\n    Then t\n",
        )
        _make_record(
            _repo,
            title="Clean",
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "specs/behavior/features/x.feature",
                },
            },
        )
        resp = check_bdd_sync(_repo)
        assert resp.checked == 1
        assert resp.feature_files_checked >= 1
        # No drift findings
        assert not any(
            f.code.startswith("BDD-SYNC-") and f.code != "BDD-SYNC-INVALID-METADATA"
            for f in resp.findings
        )

    def test_schema_version(self, _repo: ArchitectureRepository) -> None:
        resp = check_bdd_sync(_repo)
        assert resp.schema == "archledger.bdd-sync.v1"

    def test_reports_unsupported_gherkin(self, _repo: ArchitectureRepository) -> None:
        _write_feature(
            _repo,
            "specs/behavior/features/x.feature",
            "Feature: F\n  Background:\n    Given g\n",
        )
        _make_record(
            _repo,
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "specs/behavior/features/x.feature",
                },
            },
        )
        resp = check_bdd_sync(_repo)
        codes = [f.code for f in resp.findings]
        assert "BDD-SYNC-GHERKIN-UNSUPPORTED" in codes

    def test_reports_syntax_error(self, _repo: ArchitectureRepository) -> None:
        _write_feature(
            _repo,
            "specs/behavior/features/x.feature",
            "Feature:\n  Scenario: S\n    Given g\n    When w\n    Then t\n",
        )
        _make_record(
            _repo,
            bdd={
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "specs/behavior/features/x.feature",
                },
            },
        )
        resp = check_bdd_sync(_repo)
        codes = [f.code for f in resp.findings]
        assert "BDD-SYNC-GHERKIN-SYNTAX" in codes

    def test_sync_parses_each_feature_file_once(
        self, _repo: ArchitectureRepository, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_feature(
            _repo,
            "specs/behavior/features/x.feature",
            "Feature: F\n  Scenario: S1\n    Given g\n    When w\n    Then t\n"
            "  Scenario: S2\n    Given g2\n    When w2\n    Then t2\n",
        )
        _make_record(
            _repo,
            title="One",
            bdd={
                "feature": "F",
                "scenario": "S1",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "specs/behavior/features/x.feature",
                },
            },
        )
        _make_record(
            _repo,
            title="Two",
            bdd={
                "feature": "F",
                "scenario": "S2",
                "given": ["g2"],
                "when": ["w2"],
                "then": ["t2"],
                "automation": {
                    "status": "linked",
                    "feature_file": "specs/behavior/features/x.feature",
                },
            },
        )
        calls = 0
        from archledger.bdd import sync as bdd_sync

        original = bdd_sync.parse_gherkin

        def counted(text: str):  # noqa: ANN202
            nonlocal calls
            calls += 1
            return original(text)

        monkeypatch.setattr(bdd_sync, "parse_gherkin", counted)
        resp = check_bdd_sync(_repo)
        assert resp.findings == ()
        assert calls == 1
