"""Tests for archledger.bdd.validate — direct unit tests.

These test the validate module directly (not via CLI) to cover
scenarios like absent metadata, invalid automation statuses,
tag format warnings, and feature-file edge cases.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from archledger.bdd.validate import (
    validate_bdd_all,
    validate_bdd_feature_file,
    validate_bdd_record,
)
from archledger.repository import ArchitectureRepository


@pytest.fixture()
def _repo(tmp_path: Path) -> ArchitectureRepository:
    """Create an initialized repo for direct validation tests."""
    from typer.testing import CliRunner

    from archledger.cli import app
    from archledger.storage.paths import resolve_project_paths

    runner = CliRunner()
    result = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert result.exit_code == 0, result.stdout
    paths, config, _ = resolve_project_paths(tmp_path)
    return ArchitectureRepository(paths, config)


def _make_record_with_bdd(
    repo: ArchitectureRepository, bdd: dict, *, title: str = "S"
) -> str:
    """Create a record, patch bdd metadata, return its id."""
    from archledger.storage.frontmatter import (
        read_front_matter_document,
        write_front_matter_document,
    )

    record = repo.create_record("runtime_scenario", title, status="accepted")
    fm, body = read_front_matter_document(record.path)
    fm["bdd"] = bdd
    write_front_matter_document(record.path, fm, body)
    return record.id


class TestValidateBddRecord:
    """@bdd-validate-valid-record, @bdd-validate-absent-metadata, etc."""

    def test_valid_bdd_metadata_passes(self, _repo: ArchitectureRepository) -> None:
        rid = _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "linked", "feature_file": "x.feature"},
            },
        )
        resp = validate_bdd_record(_repo, rid)
        assert resp.valid
        assert not any(f.severity == "error" for f in resp.findings)

    def test_absent_bdd_metadata_is_error(self, _repo: ArchitectureRepository) -> None:
        # Create record without bdd metadata
        record = _repo.create_record("runtime_scenario", "NoBdd", status="accepted")
        resp = validate_bdd_record(_repo, record.id)
        assert not resp.valid
        codes = [f.code for f in resp.findings]
        assert "BDD-METADATA-ABSENT" in codes

    def test_incomplete_gwt_is_error(self, _repo: ArchitectureRepository) -> None:
        rid = _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": [],
                "when": ["w"],
                "then": ["t"],
            },
        )
        resp = validate_bdd_record(_repo, rid)
        assert not resp.valid
        codes = [f.code for f in resp.findings]
        assert "BDD-GWT-INCOMPLETE" in codes

    def test_invalid_automation_status_is_error(
        self, _repo: ArchitectureRepository
    ) -> None:
        rid = _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "unknown"},
            },
        )
        resp = validate_bdd_record(_repo, rid)
        # Normalize catches the bad status and reports BDD-METADATA-SHAPE;
        # validate does not see an invalid status because normalize resets to pending.
        codes = [f.code for f in resp.findings]
        assert "BDD-METADATA-SHAPE" in codes

    def test_automated_without_command_is_warning(
        self, _repo: ArchitectureRepository
    ) -> None:
        rid = _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "automated"},
            },
        )
        resp = validate_bdd_record(_repo, rid)
        codes = [f.code for f in resp.findings]
        assert "BDD-AUTOMATION-COMMAND" in codes

    def test_linked_without_feature_file_is_warning(
        self, _repo: ArchitectureRepository
    ) -> None:
        rid = _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {"status": "linked"},
            },
        )
        resp = validate_bdd_record(_repo, rid)
        codes = [f.code for f in resp.findings]
        assert "BDD-AUTOMATION-LINK" in codes

    def test_empty_or_whitespace_tag_is_warning(
        self, _repo: ArchitectureRepository
    ) -> None:
        rid = _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "tags": ["valid", "", "has space"],
            },
        )
        resp = validate_bdd_record(_repo, rid)
        codes = [f.code for f in resp.findings]
        assert "BDD-TAG-FORMAT" in codes
        tag_warnings = [f for f in resp.findings if f.code == "BDD-TAG-FORMAT"]
        # The whitespace-containing tag produces a warning; empty string tags are
        # filtered out by normalize before they reach validate.
        assert len(tag_warnings) >= 1

    def test_deprecated_feature_path_is_warning(
        self, _repo: ArchitectureRepository
    ) -> None:
        rid = _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "tests/bdd/features/old.feature",
                },
            },
        )
        resp = validate_bdd_record(_repo, rid)
        codes = [f.code for f in resp.findings]
        assert "BDD-FEATURE-PATH-CONVENTION" in codes

    def test_unsafe_feature_path_is_error(self, _repo: ArchitectureRepository) -> None:
        rid = _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
                "automation": {
                    "status": "linked",
                    "feature_file": "../escape.feature",
                },
            },
        )
        resp = validate_bdd_record(_repo, rid)
        # Normalize clears the unsafe path and reports BDD-METADATA-SHAPE;
        # validate then reports BDD-AUTOMATION-LINK because feature_file is empty
        # after normalization while status is still 'linked'.
        codes = [f.code for f in resp.findings]
        assert "BDD-METADATA-SHAPE" in codes


class TestValidateBddFeatureFile:
    """@bdd-validate-feature-file, @bdd-validate-feature-file-missing, etc."""

    def test_valid_feature_file_passes(self, _repo: ArchitectureRepository) -> None:
        feat = _repo.paths.workspace_root / "ok.feature"
        feat.write_text(
            "Feature: F\n  Scenario: A\n    Given g\n    When w\n    Then t\n",
            encoding="utf-8",
        )
        resp = validate_bdd_feature_file(_repo, "ok.feature")
        assert resp.valid
        assert len(resp.scenarios) == 1
        assert resp.scenarios[0]["name"] == "A"

    def test_missing_feature_file_is_error(self, _repo: ArchitectureRepository) -> None:
        resp = validate_bdd_feature_file(_repo, "nonexistent.feature")
        assert not resp.valid
        codes = [f.code for f in resp.findings]
        assert "BDD-FEATURE-MISSING" in codes

    def test_unsupported_gherkin_reports_line(
        self, _repo: ArchitectureRepository
    ) -> None:
        feat = _repo.paths.workspace_root / "bad.feature"
        feat.write_text("Feature: F\n  Background:\n    Given g\n", encoding="utf-8")
        resp = validate_bdd_feature_file(_repo, "bad.feature")
        assert not resp.valid
        codes = [f.code for f in resp.findings]
        assert "BDD-GHERKIN-UNSUPPORTED" in codes
        # Line number should be present
        unsupported = [f for f in resp.findings if f.code == "BDD-GHERKIN-UNSUPPORTED"]
        assert unsupported[0].line == 2

    def test_no_scenarios_is_warning(self, _repo: ArchitectureRepository) -> None:
        feat = _repo.paths.workspace_root / "empty.feature"
        feat.write_text("Feature: F\n", encoding="utf-8")
        resp = validate_bdd_feature_file(_repo, "empty.feature")
        codes = [f.code for f in resp.findings]
        assert "BDD-FEATURE-NO-SCENARIOS" in codes

    def test_deprecated_path_is_warning(self, _repo: ArchitectureRepository) -> None:
        feat = _repo.paths.workspace_root / "tests" / "bdd" / "features" / "x.feature"
        feat.parent.mkdir(parents=True, exist_ok=True)
        feat.write_text(
            "Feature: F\n  Scenario: A\n    Given g\n    When w\n    Then t\n",
            encoding="utf-8",
        )
        resp = validate_bdd_feature_file(_repo, "tests/bdd/features/x.feature")
        codes = [f.code for f in resp.findings]
        assert "BDD-FEATURE-PATH-CONVENTION" in codes

    def test_syntax_error_in_feature_file(self, _repo: ArchitectureRepository) -> None:
        feat = _repo.paths.workspace_root / "syntax.feature"
        feat.write_text("Feature: F\n  Scenario: A\n    And orphan\n", encoding="utf-8")
        resp = validate_bdd_feature_file(_repo, "syntax.feature")
        assert not resp.valid
        codes = [f.code for f in resp.findings]
        assert "BDD-GHERKIN-SYNTAX" in codes

    def test_absolute_path_is_error(self, _repo: ArchitectureRepository) -> None:
        resp = validate_bdd_feature_file(_repo, "/etc/passwd")
        assert not resp.valid
        codes = [f.code for f in resp.findings]
        assert "BDD-FEATURE-PATH" in codes

    def test_scenario_with_incomplete_gwt(self, _repo: ArchitectureRepository) -> None:
        feat = _repo.paths.workspace_root / "incomplete.feature"
        feat.write_text("Feature: F\n  Scenario: A\n    Given g\n", encoding="utf-8")
        resp = validate_bdd_feature_file(_repo, "incomplete.feature")
        codes = [f.code for f in resp.findings]
        assert "BDD-GWT-INCOMPLETE" in codes


class TestValidateBddAll:
    """@bdd-validate-all-skip-no-bdd"""

    def test_skips_records_without_bdd(self, _repo: ArchitectureRepository) -> None:
        # Create one record with bdd and one without
        _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": ["g"],
                "when": ["w"],
                "then": ["t"],
            },
            title="WithBdd",
        )
        _repo.create_record("requirement", "NoBdd", status="accepted")

        resp = validate_bdd_all(_repo)
        assert resp.target == "all"
        # Only the record with bdd should be checked
        assert resp.valid

    def test_reports_invalid_records(self, _repo: ArchitectureRepository) -> None:
        _make_record_with_bdd(
            _repo,
            {
                "feature": "F",
                "scenario": "S",
                "given": [],
                "when": [],
                "then": [],
            },
            title="Bad",
        )
        resp = validate_bdd_all(_repo)
        assert not resp.valid
        assert any(f.code == "BDD-GWT-INCOMPLETE" for f in resp.findings)
