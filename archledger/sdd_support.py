from __future__ import annotations

from collections.abc import Iterable

from archledger.model import ArchitectureRecord


def build_acceptance_index(
    records: Iterable[ArchitectureRecord],
) -> dict[str, list[ArchitectureRecord]]:
    acceptance_by_requirement: dict[str, list[ArchitectureRecord]] = {}
    for record in records:
        if record.type != "acceptance_criterion":
            continue
        requirement = record.metadata.get("requirement", "")
        if isinstance(requirement, str) and requirement.strip():
            acceptance_by_requirement.setdefault(requirement.strip(), []).append(record)
        for link in record.links:
            if link.rel == "validates":
                acceptance_by_requirement.setdefault(link.target, []).append(record)
    return acceptance_by_requirement


def classify_inline_acceptance_criteria(
    record: ArchitectureRecord,
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    raw = record.metadata.get("acceptance_criteria")
    if not isinstance(raw, list):
        return [], []
    valid: list[dict[str, object]] = []
    findings: list[tuple[str, str]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            findings.append(
                (
                    "SDD-AC-FORMAT",
                    f"Record {record.id} acceptance_criteria entry {index} "
                    "must be a mapping.",
                )
            )
            continue
        statement = item.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            findings.append(
                (
                    "SDD-AC-NO-STATEMENT",
                    f"Record {record.id} acceptance_criteria entry {index} "
                    "has no statement.",
                )
            )
            continue
        valid.append(item)
        validation = item.get("validation")
        if validation is not None and not isinstance(validation, dict):
            findings.append(
                (
                    "SDD-AC-VALIDATION-FORMAT",
                    f"Record {record.id} acceptance_criteria entry {index} "
                    "validation must be a mapping.",
                )
            )
    return valid, findings


def valid_inline_acceptance_criteria(
    record: ArchitectureRecord,
) -> list[dict[str, object]]:
    return classify_inline_acceptance_criteria(record)[0]


def has_inline_acceptance_criteria(record: ArchitectureRecord) -> bool:
    return bool(valid_inline_acceptance_criteria(record))


def requirement_has_implementation(record: ArchitectureRecord) -> bool:
    return any(ref.role == "implements" for ref in record.source_refs)


def requirement_has_validation(
    record: ArchitectureRecord,
    acceptance_by_requirement: dict[str, list[ArchitectureRecord]],
) -> bool:
    if record.test_refs:
        return True
    if any(ref.role == "validates" for ref in record.source_refs):
        return True
    for item in valid_inline_acceptance_criteria(record):
        validation = item.get("validation")
        if isinstance(validation, dict) and validation.get("command"):
            return True
    for ac_record in acceptance_by_requirement.get(record.id, []):
        if ac_record.test_refs:
            return True
        if any(ref.role == "validates" for ref in ac_record.source_refs):
            return True
        validation = ac_record.metadata.get("validation")
        if isinstance(validation, dict) and validation.get("command"):
            return True
    return False


def adr_has_traceability(record: ArchitectureRecord) -> bool:
    return bool(record.links or record.metadata.get("related") or record.source_refs)

