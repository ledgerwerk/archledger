"""Tests for archledger.bdd models and normalize_bdd_metadata."""

from __future__ import annotations

from archledger.bdd.models import (
    BDD_AUTOMATION_STATUSES,
    DEFAULT_BDD_AUTOMATION_STATUS,
    BddAutomation,
    BddExample,
)
from archledger.bdd.normalize import normalize_bdd_metadata


def test_bdd_automation_default_status_is_pending() -> None:
    automation = BddAutomation()
    assert automation.status == "pending"
    assert automation.feature_file == ""
    assert automation.scenario == ""
    assert automation.command == ""
    assert "pending" in BDD_AUTOMATION_STATUSES
    assert DEFAULT_BDD_AUTOMATION_STATUS == "pending"


def test_bdd_example_is_frozen_and_hashable() -> None:
    example = BddExample(
        feature="F",
        rule="R",
        scenario="S",
        given=("g1",),
        when=("w1",),
        then=("t1",),
    )
    assert example.tags == ()
    assert example.task_refs == ()
    assert example.acceptance_criteria == ()
    assert example.automation is None
    # frozen dataclass: attribute assignment must fail
    try:
        example.feature = "x"  # type: ignore[misc]
    except AttributeError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("BddExample must be frozen")
    # hashable (tuple sequences)
    assert hash(example) == hash(example)


def test_normalize_accepts_none_and_returns_no_example() -> None:
    example, warnings = normalize_bdd_metadata("al_runtime_0001", None)
    assert example is None
    assert warnings == []


def test_normalize_accepts_complete_bdd_block() -> None:
    example, warnings = normalize_bdd_metadata(
        "al_runtime_0001",
        {
            "feature": "Task lifecycle gates",
            "rule": "Implementation requires an accepted plan",
            "scenario": "Agent tries to implement before approval",
            "tags": ["lifecycle", "approval"],
            "given": ["a task has a proposed plan"],
            "when": ["the agent starts implementation"],
            "then": ["implementation is blocked"],
            "task_refs": ["task-0112"],
            "acceptance_criteria": ["ac-0001"],
            "automation": {
                "status": "pending",
                "feature_file": (
                    "specs/behavior/features/task-management/lifecycle.feature"
                ),
                "scenario": "Agent tries to implement before approval",
                "command": "pytest -q tests/test_task_management_lifecycle.py",
            },
        },
    )
    assert warnings == []
    assert example is not None
    assert example.feature == "Task lifecycle gates"
    assert example.rule == "Implementation requires an accepted plan"
    assert example.scenario == "Agent tries to implement before approval"
    assert example.given == ("a task has a proposed plan",)
    assert example.when == ("the agent starts implementation",)
    assert example.then == ("implementation is blocked",)
    assert example.tags == ("lifecycle", "approval")
    assert example.task_refs == ("task-0112",)
    assert example.acceptance_criteria == ("ac-0001",)
    assert example.automation == BddAutomation(
        status="pending",
        feature_file="specs/behavior/features/task-management/lifecycle.feature",
        scenario="Agent tries to implement before approval",
        command="pytest -q tests/test_task_management_lifecycle.py",
    )


def test_normalize_rejects_non_mapping() -> None:
    example, warnings = normalize_bdd_metadata("al_runtime_0001", ["not", "a", "map"])
    assert example is None
    assert any("must be a mapping" in w for w in warnings)


def test_normalize_flags_missing_required_text_fields() -> None:
    example, warnings = normalize_bdd_metadata(
        "al_runtime_0001",
        {"rule": "R"},
    )
    assert example is not None  # recoverable: shape intact
    assert any("bdd.feature is missing" in w for w in warnings)
    assert any("bdd.scenario is missing" in w for w in warnings)
    # rule is optional and present -> no warning for it
    assert not any("bdd.rule" in w for w in warnings)


def test_normalize_flags_wrong_types() -> None:
    example, warnings = normalize_bdd_metadata(
        "al_runtime_0001",
        {
            "feature": 123,
            "scenario": "  ",
            "given": "not-a-list",
            "tags": ["ok", 7, ""],
        },
    )
    assert example is not None
    assert example.feature == ""
    assert example.scenario == ""
    assert example.given == ()
    assert "ok" in example.tags and len(example.tags) == 1
    assert any("bdd.feature must be a string" in w for w in warnings)
    assert any("bdd.scenario is empty" in w for w in warnings)
    assert any("bdd.given must be a list of strings" in w for w in warnings)
    assert any("bdd.tags entry 2 must be a non-empty string" in w for w in warnings)
    assert any("bdd.tags entry 3 must be a non-empty string" in w for w in warnings)


def test_normalize_automation_default_status_when_missing() -> None:
    example, warnings = normalize_bdd_metadata(
        "al_runtime_0001",
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {},
        },
    )
    assert example is not None
    assert example.automation is not None
    assert example.automation.status == "pending"
    assert not any("automation.status" in w for w in warnings)


def test_normalize_automation_rejects_invalid_status() -> None:
    example, warnings = normalize_bdd_metadata(
        "al_runtime_0001",
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"status": "done"},
        },
    )
    assert example is not None
    assert example.automation is not None
    assert example.automation.status == "pending"  # reset to default
    assert any("automation.status 'done' is not one of" in w for w in warnings)


def test_normalize_automation_feature_file_must_be_safe_relative_posix() -> None:
    example, warnings = normalize_bdd_metadata(
        "al_runtime_0001",
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"feature_file": "../escape.feature"},
        },
    )
    assert example is not None
    assert example.automation is not None
    assert example.automation.feature_file == ""
    assert any("must not contain '..'" in w for w in warnings)


def test_normalize_automation_feature_file_accepts_relative_posix() -> None:
    example, warnings = normalize_bdd_metadata(
        "al_runtime_0001",
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {
                "feature_file": "specs/behavior/features/task-management/x.feature"
            },
        },
    )
    assert example is not None
    assert example.automation is not None
    assert (
        example.automation.feature_file
        == "specs/behavior/features/task-management/x.feature"
    )
    assert not any("feature_file" in w for w in warnings)


def test_normalize_automation_non_mapping_is_fatal() -> None:
    example, warnings = normalize_bdd_metadata(
        "al_runtime_0001",
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": ["nope"],
        },
    )
    assert example is None
    assert any("bdd.automation must be a mapping" in w for w in warnings)


def test_normalize_automation_command_must_be_string_and_never_executed() -> None:
    example, warnings = normalize_bdd_metadata(
        "al_runtime_0001",
        {
            "feature": "F",
            "scenario": "S",
            "given": ["g"],
            "when": ["w"],
            "then": ["t"],
            "automation": {"command": 42},
        },
    )
    assert example is not None
    assert example.automation is not None
    assert example.automation.command == ""
    assert any("bdd.automation.command must be a string" in w for w in warnings)
