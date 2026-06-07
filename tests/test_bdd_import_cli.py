"""Tests for archledger bdd import CLI command."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.frontmatter import read_front_matter_document

runner = CliRunner()


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout


def _write_feature(tmp_path: Path, name: str, content: str) -> str:
    """Write a feature file and return the relative path."""
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return name


def test_bdd_import_creates_records_from_feature(tmp_path: Path) -> None:
    """ac-0008: import creates one record per scenario."""
    _init(tmp_path)
    rel = _write_feature(
        tmp_path,
        "test.feature",
        "Feature: F\n  Scenario: A\n    Given X\n    When Y\n    Then Z\n",
    )
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
            "proposed",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.bdd-import.v1"
    assert len(payload["created_records"]) == 1
    rec = payload["created_records"][0]
    assert rec["type"] == "runtime_scenario"
    assert rec["title"] == "A"


def test_bdd_import_writes_bdd_metadata(tmp_path: Path) -> None:
    """ac-0008: imported records have correct bdd metadata and source_refs."""
    _init(tmp_path)
    rel = _write_feature(
        tmp_path,
        "lifecycle.feature",
        textwrap.dedent("""\
            @tag1
            Feature: Task lifecycle
              Rule: Must have plan
                @tag2
                Scenario: Before approval
                  Given plan exists
                  When agent starts
                  Then blocked
        """),
    )
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
        ],
    )
    assert result.exit_code == 0, result.stdout
    rec_path = Path(json.loads(result.stdout)["result"]["created_records"][0]["path"])
    metadata, body = read_front_matter_document(rec_path)
    bdd = metadata["bdd"]
    assert bdd["feature"] == "Task lifecycle"
    assert bdd["rule"] == "Must have plan"
    assert bdd["scenario"] == "Before approval"
    assert "tag1" in bdd["tags"]
    assert "tag2" in bdd["tags"]
    assert bdd["given"] == ["plan exists"]
    assert bdd["when"] == ["agent starts"]
    assert bdd["then"] == ["blocked"]
    # Imported scenarios are linked to their feature file by definition.
    assert bdd["automation"]["status"] == "linked"
    assert bdd["automation"]["feature_file"] == rel
    assert bdd["automation"]["scenario"] == "Before approval"
    # source_ref for the feature file
    assert any(ref["role"] == "documents" for ref in metadata.get("source_refs", []))
    # Body contains scenario content
    assert "## Scenario" in body
    assert "Given plan exists" in body


def test_bdd_import_writes_body_with_correct_gwt_prefixes(tmp_path: Path) -> None:
    """Body uses Given/And for multiple Given steps."""
    _init(tmp_path)
    rel = _write_feature(
        tmp_path,
        "test.feature",
        "Feature: F\n"
        "  Scenario: S\n"
        "    Given a\n"
        "    And b\n"
        "    When c\n"
        "    Then d\n"
        "    And e\n",
    )
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "import",
            rel,
        ],
    )
    assert result.exit_code == 0, result.stdout
    rec_path = Path(json.loads(result.stdout)["result"]["created_records"][0]["path"])
    _, body = read_front_matter_document(rec_path)
    assert "Given a" in body
    assert "And b" in body
    assert "And e" in body


def test_bdd_import_quality_scenario(tmp_path: Path) -> None:
    """ac-0008: import with kind quality-scenario works."""
    _init(tmp_path)
    rel = _write_feature(
        tmp_path,
        "test.feature",
        (
            "Feature: Perf\n"
            "  Scenario: Latency\n"
            "    Given load\n"
            "    When measure\n"
            "    Then ok\n"
        ),
    )
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
            "quality-scenario",
        ],
    )
    assert result.exit_code == 0, result.stdout
    rec = json.loads(result.stdout)["result"]["created_records"][0]
    assert rec["type"] == "quality_scenario"


def test_bdd_import_refuses_unsafe_feature_path(tmp_path: Path) -> None:
    """ac-0009: import refuses paths with '..'."""
    _init(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "import",
            "../escape.feature",
        ],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert (
        "must not contain" in payload["error"]["message"].lower()
        or ".." in payload["error"]["message"]
    )


def test_bdd_import_refuses_unsupported_gherkin(tmp_path: Path) -> None:
    """ac-0009: import refuses unsupported Gherkin constructs."""
    _init(tmp_path)
    rel = _write_feature(
        tmp_path,
        "bad.feature",
        "Feature: F\n  Background:\n    Given X\n",
    )
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "bdd",
            "import",
            rel,
        ],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert (
        "not supported" in payload["error"]["message"].lower()
        or "background" in payload["error"]["message"].lower()
    )


def test_bdd_import_fixture_feature(tmp_path: Path) -> None:
    """ac-0008: import the full lifecycle fixture."""
    _init(tmp_path)
    fixture = (
        Path(__file__).parent.parent
        / "tests"
        / "fixtures"
        / "bdd"
        / "lifecycle.feature"
    )
    if not fixture.exists():
        pytest.skip("Fixture not present.")
    # Copy fixture into tmp_path for relative path
    dest = tmp_path / "tests" / "fixtures" / "bdd" / "lifecycle.feature"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(fixture.read_bytes())
    rel = "tests/fixtures/bdd/lifecycle.feature"
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
            "proposed",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.bdd-import.v1"
    assert len(payload["created_records"]) == 2


def test_bdd_import_json_schema_matches() -> None:
    """ac-0010: the JSON schema target exists and is loadable."""
    from archledger.jsonschemas import SCHEMA_FILES, load_json_schema

    assert "bdd-import" in SCHEMA_FILES
    schema = load_json_schema("bdd-import")
    assert schema["title"] == "Archledger BDD import result"
    assert "created_records" in schema["required"]


def test_bdd_import_no_cucumber_dependency() -> None:
    """ac-0013: no Cucumber/pytest-bdd is imported at module level."""
    import archledger.bdd

    for name in archledger.bdd.__dict__:
        assert "cucumber" not in name.lower()
        assert "pytest_bdd" not in name.lower()


# ---- P0: import body replacement + automation fields + structured errors ----


def test_bdd_import_accepted_record_does_not_keep_template_placeholder(
    tmp_path: Path,
) -> None:
    """P0: an accepted imported record must not keep the template placeholder body."""
    _init(tmp_path)
    rel = _write_feature(
        tmp_path,
        "test.feature",
        "Feature: F\n  Scenario: A\n    Given X\n    When Y\n    Then Z\n",
    )
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
    rec_path = Path(json.loads(result.stdout)["result"]["created_records"][0]["path"])
    metadata, body = read_front_matter_document(rec_path)
    # Placeholder snippets from checks.PLACEHOLDER_SNIPPETS must be gone.
    from archledger.checks import PLACEHOLDER_SNIPPETS

    stripped = body.strip()
    for snippet in PLACEHOLDER_SNIPPETS:
        assert snippet not in stripped, f"placeholder {snippet!r} still present"
    # And the scenario body is present.
    assert "Given X" in body
    assert "Then Z" in body


def test_bdd_import_sets_automation_feature_file_and_scenario(tmp_path: Path) -> None:
    """P0: imported records populate automation.feature_file and automation.scenario."""
    _init(tmp_path)
    rel = _write_feature(
        tmp_path,
        "tests/bdd/features/lifecycle.feature",
        "Feature: Task lifecycle\n"
        "  Scenario: Blocked\n"
        "    Given g\n    When w\n    Then t\n",
    )
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
        ],
    )
    assert result.exit_code == 0, result.stdout
    rec_path = Path(json.loads(result.stdout)["result"]["created_records"][0]["path"])
    metadata, _body = read_front_matter_document(rec_path)
    auto = metadata["bdd"]["automation"]
    assert auto["feature_file"] == rel
    assert auto["scenario"] == "Blocked"


def test_bdd_import_sets_automation_status_linked_by_default(tmp_path: Path) -> None:
    """P0: imported records default automation.status to 'linked'."""
    _init(tmp_path)
    rel = _write_feature(
        tmp_path,
        "test.feature",
        "Feature: F\n  Scenario: A\n    Given g\n    When w\n    Then t\n",
    )
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "import", rel],
    )
    assert result.exit_code == 0, result.stdout
    rec_path = Path(json.loads(result.stdout)["result"]["created_records"][0]["path"])
    metadata, _body = read_front_matter_document(rec_path)
    assert metadata["bdd"]["automation"]["status"] == "linked"


def test_bdd_import_reports_gherkin_line_number_in_json_error(tmp_path: Path) -> None:
    """P0: JSON error preserves structured detail (line/construct/feature_file)."""
    _init(tmp_path)
    rel = _write_feature(
        tmp_path,
        "bad.feature",
        "Feature: F\n  Background:\n    Given X\n",
    )
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "bdd", "import", rel],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    err = payload["error"]
    # Structured error detail must carry the line number and the construct.
    details = err.get("details", {})
    assert details.get("line") == 2 or "line" in str(details)
    assert details.get("construct") == "Background:" or "Background" in str(details)
    assert details.get("feature_file") == rel or rel in str(details)
