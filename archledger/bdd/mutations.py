from __future__ import annotations

from archledger.bdd.models import BDD_AUTOMATION_STATUSES
from archledger.errors import ValidationError
from archledger.source_refs import RelativePosixPathError, validate_relative_posix_path


def build_bdd_set_block(
    record_id: str,
    existing: object,
    *,
    feature: str | None = None,
    rule: str | None = None,
    scenario: str | None = None,
    given: list[str] | None = None,
    when: list[str] | None = None,
    then: list[str] | None = None,
    tag: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
    task_refs: list[str] | None = None,
    automation_status: str | None = None,
    feature_file: str | None = None,
    command: str | None = None,
) -> dict[str, object]:
    block = dict(existing) if isinstance(existing, dict) else {}
    if feature is not None:
        block["feature"] = feature
    if rule is not None:
        block["rule"] = rule
    if scenario is not None:
        block["scenario"] = scenario
    if given is not None:
        block["given"] = list(given)
    if when is not None:
        block["when"] = list(when)
    if then is not None:
        block["then"] = list(then)
    if tag is not None:
        block["tags"] = list(tag)
    if acceptance_criteria is not None:
        block["acceptance_criteria"] = list(acceptance_criteria)
    if task_refs is not None:
        block["task_refs"] = list(task_refs)

    automation = _existing_automation(block)
    if automation_status is not None:
        automation["status"] = automation_status
    if feature_file is not None:
        automation["feature_file"] = feature_file
    if command is not None:
        automation["command"] = command
    if automation:
        block["automation"] = automation

    return validate_bdd_mutation_block(block, record_id=record_id)


def build_bdd_link_block(
    record_id: str,
    existing: object,
    *,
    feature_file: str | None = None,
    scenario: str | None = None,
    command: str | None = None,
    status: str | None = None,
    has_existing_test_ref: bool,
    has_new_test_ref: bool,
) -> dict[str, object]:
    if not isinstance(existing, dict):
        raise ValidationError(
            f"Record {record_id} has no bdd metadata. Run 'bdd set' first."
        )

    block = dict(existing)
    automation = _existing_automation(block)
    if feature_file is not None:
        automation["feature_file"] = feature_file
    if scenario is not None:
        automation["scenario"] = scenario
    if command is not None:
        automation["command"] = command
    if status is not None:
        automation["status"] = status
    elif feature_file and automation.get("status") in ("pending", "", None):
        automation["status"] = "linked"

    has_command = bool(automation.get("command"))
    if automation.get("status") == "automated" and not (
        has_command or has_existing_test_ref or has_new_test_ref
    ):
        raise ValidationError(
            "bdd link with --status automated requires --command, --test, "
            "or existing test_refs."
        )

    block["automation"] = automation
    return validate_bdd_mutation_block(block, record_id=record_id)


def validate_bdd_mutation_block(
    block: dict[str, object],
    *,
    record_id: str,
) -> dict[str, object]:
    normalized = dict(block)
    automation = normalized.get("automation")
    if automation is None:
        return normalized
    if not isinstance(automation, dict):
        raise ValidationError(f"Record {record_id} bdd.automation must be a mapping.")

    normalized_automation = dict(automation)
    _validate_automation_text_field(normalized_automation, "status", record_id)
    _validate_automation_text_field(normalized_automation, "feature_file", record_id)
    _validate_automation_text_field(normalized_automation, "scenario", record_id)
    _validate_automation_text_field(normalized_automation, "command", record_id)

    status = normalized_automation.get("status")
    if status:
        status_text = str(status).strip()
        if status_text not in BDD_AUTOMATION_STATUSES:
            raise ValidationError(
                f"Record {record_id} bdd.automation.status must be one of "
                f"{sorted(BDD_AUTOMATION_STATUSES)}."
            )
        normalized_automation["status"] = status_text

    feature_file = normalized_automation.get("feature_file")
    if feature_file:
        try:
            normalized_automation["feature_file"] = validate_relative_posix_path(
                str(feature_file),
                field_name=f"Record {record_id} bdd.automation.feature_file",
            )
        except RelativePosixPathError as exc:
            raise ValidationError(str(exc)) from exc

    normalized["automation"] = normalized_automation
    return normalized


def parse_test_ref_entry(entry: str, *, record_id: str) -> tuple[str, str]:
    raw = entry.strip()
    test_path, _separator, nodeid = raw.partition("::")
    if not test_path.strip():
        raise ValidationError(f"Record {record_id} test_refs path must be a string.")
    try:
        normalized_path = validate_relative_posix_path(
            test_path.strip(),
            field_name=f"Record {record_id} test_refs path",
        )
    except RelativePosixPathError as exc:
        raise ValidationError(str(exc)) from exc
    return normalized_path, nodeid.strip()


def _existing_automation(block: dict[str, object]) -> dict[str, object]:
    raw = block.get("automation")
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def _validate_automation_text_field(
    automation: dict[str, object], field: str, record_id: str
) -> None:
    if field not in automation or automation[field] is None:
        return
    value = automation[field]
    if not isinstance(value, str):
        raise ValidationError(
            f"Record {record_id} bdd.automation.{field} must be a string."
        )
    automation[field] = value.strip()

