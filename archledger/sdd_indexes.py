from __future__ import annotations

from dataclasses import dataclass

from archledger.model import ArchitectureRecord
from archledger.sdd_support import (
    adr_has_traceability,
    build_acceptance_index,
    has_inline_acceptance_criteria,
    requirement_has_implementation,
    requirement_has_validation,
)


@dataclass(frozen=True, slots=True)
class SddCoverageSnapshot:
    accepted_requirements_with_ac: int
    accepted_requirements_with_implementation_refs: int
    accepted_requirements_with_validation: int
    accepted_adrs_with_traceability: int


def build_sdd_coverage_snapshot(
    records: list[ArchitectureRecord],
) -> tuple[dict[str, list[ArchitectureRecord]], SddCoverageSnapshot]:
    acceptance_by_requirement = build_acceptance_index(records)
    accepted_requirements = [
        record
        for record in records
        if record.type == "requirement" and record.status == "accepted"
    ]
    accepted_adrs = [
        record
        for record in records
        if record.type == "adr" and record.status == "accepted"
    ]
    return acceptance_by_requirement, SddCoverageSnapshot(
        accepted_requirements_with_ac=sum(
            1
            for record in accepted_requirements
            if has_inline_acceptance_criteria(record)
            or record.id in acceptance_by_requirement
        ),
        accepted_requirements_with_implementation_refs=sum(
            1
            for record in accepted_requirements
            if requirement_has_implementation(record)
        ),
        accepted_requirements_with_validation=sum(
            1
            for record in accepted_requirements
            if requirement_has_validation(record, acceptance_by_requirement)
        ),
        accepted_adrs_with_traceability=sum(
            1 for record in accepted_adrs if adr_has_traceability(record)
        ),
    )
