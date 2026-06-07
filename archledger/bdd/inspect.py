"""BDD inspection helpers for ``archledger bdd list`` and ``archledger bdd status``.

These read normalized BDD metadata across records to produce listing and
coverage summaries. They reuse :func:`normalize_bdd_metadata` so the reported
state always matches what the SDD engine sees.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from archledger.bdd.normalize import normalize_bdd_metadata
from archledger.repository import ArchitectureRepository


@dataclass(frozen=True, slots=True)
class BddListEntry:
    """One row of ``archledger bdd list``."""

    record_id: str
    status: str
    feature: str
    rule: str
    scenario: str
    automation_status: str
    feature_file: str
    command_present: bool
    valid: bool


@dataclass(frozen=True, slots=True)
class BddListResponse:
    schema: str = "archledger.bdd-list.v1"
    entries: tuple[BddListEntry, ...] = ()
    count: int = 0


def list_bdd_records(
    repo: ArchitectureRepository,
    *,
    status_filter: str | None = None,
    automation_filter: str | None = None,
    feature_filter: str | None = None,
) -> BddListResponse:
    """List all records carrying ``bdd`` metadata with optional filters."""
    records = repo.load_all_records(include_sections=True)
    entries: list[BddListEntry] = []
    for record in records:
        raw_bdd = record.metadata.get("bdd")
        if raw_bdd is None:
            continue
        example, warnings = normalize_bdd_metadata(record.id, raw_bdd)
        valid = example is not None and not warnings
        if example is None:
            entry = BddListEntry(
                record_id=record.id,
                status=record.status,
                feature="",
                rule="",
                scenario="",
                automation_status="",
                feature_file="",
                command_present=False,
                valid=False,
            )
        else:
            auto = example.automation
            entry = BddListEntry(
                record_id=record.id,
                status=record.status,
                feature=example.feature,
                rule=example.rule,
                scenario=example.scenario,
                automation_status=auto.status if auto else "",
                feature_file=auto.feature_file if auto else "",
                command_present=bool(auto and auto.command),
                valid=valid,
            )
        if status_filter and entry.status != status_filter:
            continue
        if automation_filter and entry.automation_status != automation_filter:
            continue
        if feature_filter and entry.feature != feature_filter:
            continue
        entries.append(entry)
    return BddListResponse(entries=tuple(entries), count=len(entries))


@dataclass(frozen=True, slots=True)
class BddStatusResponse:
    schema: str = "archledger.bdd-status.v1"
    totals: dict[str, int] = field(default_factory=dict)
    coverage: dict[str, dict[str, int]] = field(default_factory=dict)


def bdd_status_summary(repo: ArchitectureRepository) -> BddStatusResponse:
    """Summarize BDD coverage: complete GWT, linked features, automation."""
    records = repo.load_all_records(include_sections=True)
    total = 0
    invalid = 0
    complete_gwt = 0
    linked_features = 0
    automated = 0
    pending = 0
    by_automation: dict[str, int] = {}
    for record in records:
        raw_bdd = record.metadata.get("bdd")
        if raw_bdd is None:
            continue
        total += 1
        example, warnings = normalize_bdd_metadata(record.id, raw_bdd)
        if example is None or warnings:
            invalid += 1
            continue
        if example.given and example.when and example.then:
            complete_gwt += 1
        auto = example.automation
        status = auto.status if auto else "pending"
        by_automation[status] = by_automation.get(status, 0) + 1
        if auto and auto.feature_file:
            linked_features += 1
        if status == "automated":
            automated += 1
        if status == "pending":
            pending += 1

    def _dim(covered: int) -> dict[str, int]:
        return {"covered": covered, "total": total}

    return BddStatusResponse(
        totals={
            "examples": total,
            "invalid_metadata": invalid,
        },
        coverage={
            "complete_gwt": _dim(complete_gwt),
            "linked_feature_files": _dim(linked_features),
            "automated": _dim(automated),
            "pending": _dim(pending),
        },
    )


def status_entry_dicts(response: BddListResponse) -> list[dict[str, Any]]:
    return [
        {
            "record_id": e.record_id,
            "status": e.status,
            "feature": e.feature,
            "rule": e.rule,
            "scenario": e.scenario,
            "automation_status": e.automation_status,
            "feature_file": e.feature_file,
            "command_present": e.command_present,
            "valid": e.valid,
        }
        for e in response.entries
    ]


__all__ = [
    "BddListEntry",
    "BddListResponse",
    "BddStatusResponse",
    "bdd_status_summary",
    "list_bdd_records",
    "status_entry_dicts",
]
