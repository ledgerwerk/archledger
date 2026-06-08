"""Trace a record through its linked requirements, ADRs, source refs,
tests, and risks.

``trace`` answers: What requirement is this implementing? Which ADR
constrains it? Which files implement it? Which tests validate it?
Which risks remain open?
"""

from __future__ import annotations

from typing import Any

from archledger.model import ArchitectureRecord
from archledger.repository import ArchitectureRepository


def build_trace(repo: ArchitectureRepository, record_id: str) -> dict[str, Any]:
    records = repo.load_all_records(include_sections=True)
    by_id = {r.id: r for r in records}

    root = by_id.get(record_id)
    if root is None:
        return {
            "schema": "archledger.trace.v1",
            "root": None,
            "error": f"Record not found: {record_id}",
        }

    # Gather linked records by walking links both directions
    outgoing: list[dict[str, Any]] = []
    incoming: list[dict[str, Any]] = []
    requirements: list[ArchitectureRecord] = []
    acceptance_criteria: list[ArchitectureRecord] = []
    decisions: list[ArchitectureRecord] = []
    constraints: list[ArchitectureRecord] = []
    risks: list[ArchitectureRecord] = []
    source_refs: list[dict[str, Any]] = []
    test_refs: list[dict[str, Any]] = []

    # Outgoing links from root
    for link in root.links:
        outgoing.append({"rel": link.rel, "target": link.target, "reason": link.reason})
        target = by_id.get(link.target)
        if target is not None:
            _categorize(
                target, requirements, acceptance_criteria, decisions, constraints, risks
            )

    # Incoming links to root
    for r in records:
        for link in r.links:
            if link.target == record_id:
                incoming.append(
                    {"rel": link.rel, "source": r.id, "reason": link.reason}
                )
                _categorize(
                    r, requirements, acceptance_criteria, decisions, constraints, risks
                )

    # Source refs
    for ref in root.source_refs:
        source_refs.append(
            {
                "path": ref.path,
                "symbols": list(ref.symbols),
                "role": ref.role,
            }
        )

    # Test refs
    for tr in root.test_refs:
        test_refs.append(
            {
                "path": tr.path,
                "nodeid": tr.nodeid,
                "role": tr.role,
            }
        )

    # Related records via metadata (legacy)
    related = root.metadata.get("related")
    if isinstance(related, list):
        for item in related:
            rid = str(item)
            related_record = by_id.get(rid)
            if related_record is not None:
                _categorize(
                    related_record,
                    requirements,
                    acceptance_criteria,
                    decisions,
                    constraints,
                    risks,
                )

    return {
        "schema": "archledger.trace.v1",
        "root": {
            "id": root.id,
            "type": root.type,
            "title": root.title,
            "status": root.status,
            "metadata": dict(root.metadata),
        },
        "requirements": [_record_ref(r) for r in requirements],
        "acceptance_criteria": [_record_ref(r) for r in acceptance_criteria],
        "decisions": [_record_ref(r) for r in decisions],
        "constraints": [_record_ref(r) for r in constraints],
        "risks": [_record_ref(r) for r in risks],
        "source_refs": source_refs,
        "test_refs": test_refs,
        "incoming_links": incoming,
        "outgoing_links": outgoing,
    }


def _record_ref(r: ArchitectureRecord) -> dict[str, Any]:
    return {"id": r.id, "type": r.type, "title": r.title, "status": r.status}


def _categorize(
    r: ArchitectureRecord,
    requirements: list,
    acceptance_criteria: list,
    decisions: list,
    constraints: list,
    risks: list,
) -> None:
    if r.type == "requirement":
        requirements.append(r)
    elif r.type == "acceptance_criterion":
        acceptance_criteria.append(r)
    elif r.type == "adr":
        decisions.append(r)
    elif r.type == "constraint":
        constraints.append(r)
    elif r.type == "risk":
        risks.append(r)


__all__ = ["build_trace"]
