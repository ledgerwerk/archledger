"""SDD (Specification-Driven Design) policy engine.

This module evaluates SDD traceability contracts on loaded records
without depending on ``cli.py``.  The CLI sub-app and test suites
call into this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archledger.checks import PLACEHOLDER_SNIPPETS
from archledger.model import (
    VALID_SOURCE_REF_ROLES,
    ArchitectureRecord,
)
from archledger.repository import ArchitectureRepository

# ── data classes ────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class SddOptions:
    strict: bool = False
    require_implementation_refs: bool = True
    require_test_refs: bool = True
    include_draft: bool = False
    include_superseded: bool = False


@dataclass(frozen=True, slots=True)
class SddFinding:
    level: str  # "error" or "warning"
    code: str  # e.g. "SDD-REQ-AC"
    message: str
    record_id: str | None = None
    path: Path | None = None


@dataclass(frozen=True, slots=True)
class SddCheckResult:
    errors: tuple[SddFinding, ...]
    warnings: tuple[SddFinding, ...]
    summary: dict[str, int]

    def has_failures(self, *, strict: bool) -> bool:
        return bool(self.errors) or (strict and bool(self.warnings))


@dataclass(frozen=True, slots=True)
class SddStatusResult:
    profile: str
    counts: dict[str, int]
    coverage: dict[str, int]


# ── public API ──────────────────────────────────────────────────────────


def check_sdd(repo: ArchitectureRepository, *, options: SddOptions) -> SddCheckResult:
    records = repo.load_all_records(include_sections=True)
    return check_sdd_records(records, repo.paths.workspace_root, options=options)


def check_sdd_records(  # noqa: C901
    records: list[ArchitectureRecord],
    workspace_root: Path,
    *,
    options: SddOptions,
) -> SddCheckResult:
    errors: list[SddFinding] = []
    warnings: list[SddFinding] = []

    records_by_id = {r.id: r for r in records}
    records_by_type: dict[str, list[ArchitectureRecord]] = {}
    for r in records:
        records_by_type.setdefault(r.type, []).append(r)

    # Build a lookup: requirement_id -> list of acceptance_criterion records
    acceptance_by_requirement: dict[str, list[ArchitectureRecord]] = {}
    for r in records_by_type.get("acceptance_criterion", []):
        req = r.metadata.get("requirement", "")
        if isinstance(req, str) and req.strip():
            acceptance_by_requirement.setdefault(req.strip(), []).append(r)
        # Also check links for validates rel pointing to a requirement
        for link in r.links:
            if link.rel == "validates":
                acceptance_by_requirement.setdefault(link.target, []).append(r)

    # Process waivers
    waivers_by_record: dict[str, set[str]] = {}
    for r in records:
        if not options.include_draft and r.status == "draft":
            continue
        raw_waivers = r.metadata.get("sdd") or {}
        if not isinstance(raw_waivers, dict):
            raw_waivers = {}
        raw_waiver_list = raw_waivers.get("waivers", [])
        if not isinstance(raw_waiver_list, list):
            continue
        for w in raw_waiver_list:
            if not isinstance(w, dict):
                continue
            rule = w.get("rule", "")
            reason = w.get("reason", "")
            if not isinstance(rule, str) or not rule.strip():
                continue
            if not isinstance(reason, str) or not reason.strip():
                errors.append(
                    SddFinding(
                        level="error",
                        code="SDD-WAIVER-NO-REASON",
                        message=f"Record {r.id} has waiver for {rule} but no reason.",
                        record_id=r.id,
                        path=r.path,
                    )
                )
                continue
            waivers_by_record.setdefault(r.id, set()).add(rule.strip())

    def has_waiver(record_id: str, rule: str) -> bool:
        return rule in waivers_by_record.get(record_id, set())

    def add_error(code: str, msg: str, rid: str, path: Path | None = None) -> None:
        errors.append(
            SddFinding(level="error", code=code, message=msg, record_id=rid, path=path)
        )

    def add_warning(code: str, msg: str, rid: str, path: Path | None = None) -> None:
        warnings.append(
            SddFinding(
                level="warning", code=code, message=msg, record_id=rid, path=path
            )
        )

    # ── Per-record checks ───────────────────────────────────────────────

    for r in records:
        if not options.include_draft and r.status == "draft":
            continue
        if not options.include_superseded and r.status == "superseded":
            continue

        # SDD-PLACEHOLDER: accepted non-section records
        if r.type != "section" and r.status == "accepted":
            stripped_body = r.body.strip()
            if stripped_body and any(
                snippet in stripped_body for snippet in PLACEHOLDER_SNIPPETS
            ):
                if not has_waiver(r.id, "SDD-PLACEHOLDER"):
                    add_error(
                        "SDD-PLACEHOLDER",
                        f"Record {r.id} has placeholder body.",
                        r.id,
                        r.path,
                    )

        # SDD-SOURCE-REF-ROLE: invalid roles
        for ref in r.source_refs:
            if ref.role and ref.role not in VALID_SOURCE_REF_ROLES:
                add_warning(
                    "SDD-SOURCE-REF-ROLE",
                    f"Record {r.id} source_ref has unknown role: {ref.role!r}.",
                    r.id,
                    r.path,
                )

        for missing_path in _missing_reference_paths(
            r.metadata.get("source_refs"), workspace_root
        ):
            if not has_waiver(r.id, "SDD-SOURCE-REF-EXISTS"):
                add_error(
                    "SDD-SOURCE-REF-EXISTS",
                    f"Record {r.id} source_ref path does not exist: {missing_path}",
                    r.id,
                    r.path,
                )

        for missing_path in _missing_reference_paths(
            r.metadata.get("test_refs"), workspace_root
        ):
            if not has_waiver(r.id, "SDD-TEST-REF-EXISTS"):
                add_error(
                    "SDD-TEST-REF-EXISTS",
                    f"Record {r.id} test_ref path does not exist: {missing_path}",
                    r.id,
                    r.path,
                )

        # SDD-LINK-TARGET: link targets must exist (only for accepted records)
        if r.status == "accepted":
            for link in r.links:
                if link.target not in records_by_id:
                    add_error(
                        "SDD-LINK-TARGET",
                        f"Record {r.id} link target {link.target!r} does not exist.",
                        r.id,
                        r.path,
                    )

        # ── Type-specific checks ────────────────────────────────────────

        if r.type == "requirement" and r.status == "accepted":
            # SDD-REQ-AC
            if not has_waiver(r.id, "SDD-REQ-AC"):
                has_ac = (
                    _has_inline_acceptance_criteria(r)
                    or r.id in acceptance_by_requirement
                )
                if not has_ac:
                    add_error(
                        "SDD-REQ-AC",
                        f"Accepted requirement {r.id} has no acceptance criteria.",
                        r.id,
                        r.path,
                    )

            # SDD-REQ-IMPL
            if options.require_implementation_refs and not has_waiver(
                r.id, "SDD-REQ-IMPL"
            ):
                has_impl = any(ref.role == "implements" for ref in r.source_refs)
                if not has_impl:
                    add_error(
                        "SDD-REQ-IMPL",
                        f"Accepted requirement {r.id} has no implementation "
                        "source_refs.",
                        r.id,
                        r.path,
                    )

            # SDD-REQ-TEST
            if options.require_test_refs and not has_waiver(r.id, "SDD-REQ-TEST"):
                has_test = _has_validation(r, acceptance_by_requirement, records_by_id)
                if not has_test:
                    add_error(
                        "SDD-REQ-TEST",
                        f"Accepted requirement {r.id} has no validation.",
                        r.id,
                        r.path,
                    )

        if r.type == "adr" and r.status == "accepted":
            if not has_waiver(r.id, "SDD-ADR-LINK"):
                has_traceability = (
                    bool(r.links)
                    or bool(r.metadata.get("related"))
                    or bool(r.source_refs)
                )
                if not has_traceability:
                    add_error(
                        "SDD-ADR-LINK",
                        f"Accepted ADR {r.id} has no traceability.",
                        r.id,
                        r.path,
                    )

        if r.type == "quality_scenario" and r.status == "accepted":
            if not has_waiver(r.id, "SDD-QS-COMPLETE"):
                missing = _qs_missing_fields(r)
                if missing:
                    add_error(
                        "SDD-QS-COMPLETE",
                        f"Accepted quality_scenario {r.id} is missing: "
                        f"{', '.join(missing)}.",
                        r.id,
                        r.path,
                    )

            if not has_waiver(r.id, "SDD-QS-MEASURABLE"):
                resp_measure = r.metadata.get("response_measure", "")
                if isinstance(resp_measure, str) and resp_measure.strip():
                    if not _looks_measurable(resp_measure):
                        add_warning(
                            "SDD-QS-MEASURABLE",
                            f"Quality_scenario {r.id} response_measure is not "
                            "measurable.",
                            r.id,
                            r.path,
                        )

    # ── Summary ─────────────────────────────────────────────────────────

    summary = {
        "records_checked": len(records),
        "accepted_requirements": len(
            [r for r in records if r.type == "requirement" and r.status == "accepted"]
        ),
        "acceptance_criteria": len(
            [r for r in records if r.type == "acceptance_criterion"]
        ),
        "errors": len(errors),
        "warnings": len(warnings),
    }

    return SddCheckResult(
        errors=tuple(errors), warnings=tuple(warnings), summary=summary
    )


def check_sdd_status(repo: ArchitectureRepository) -> SddStatusResult:
    records = repo.load_all_records(include_sections=True)
    profile = repo.config.profile

    counts: dict[str, int] = {
        "requirements": 0,
        "accepted_requirements": 0,
        "acceptance_criteria": 0,
        "adrs": 0,
        "quality_scenarios": 0,
        "risks": 0,
    }
    for r in records:
        if r.type == "requirement":
            counts["requirements"] += 1
            if r.status == "accepted":
                counts["accepted_requirements"] += 1
        elif r.type == "acceptance_criterion":
            counts["acceptance_criteria"] += 1
        elif r.type == "adr":
            counts["adrs"] += 1
        elif r.type == "quality_scenario":
            counts["quality_scenarios"] += 1
        elif r.type == "risk":
            counts["risks"] += 1

    # Build acceptance_by_requirement (same logic as check)
    acceptance_by_requirement: dict[str, list[ArchitectureRecord]] = {}
    for r in records:
        if r.type == "acceptance_criterion":
            req = r.metadata.get("requirement", "")
            if isinstance(req, str) and req.strip():
                acceptance_by_requirement.setdefault(req.strip(), []).append(r)
            for link in r.links:
                if link.rel == "validates":
                    acceptance_by_requirement.setdefault(link.target, []).append(r)

    accepted_reqs = [
        r for r in records if r.type == "requirement" and r.status == "accepted"
    ]

    with_ac = sum(
        1
        for r in accepted_reqs
        if _has_inline_acceptance_criteria(r) or r.id in acceptance_by_requirement
    )
    with_impl = sum(
        1
        for r in accepted_reqs
        if any(ref.role == "implements" for ref in r.source_refs)
    )
    with_test = sum(
        1
        for r in accepted_reqs
        if _has_validation(r, acceptance_by_requirement, {r.id: r for r in records})
    )

    accepted_adrs = [r for r in records if r.type == "adr" and r.status == "accepted"]
    with_trace = sum(
        1
        for r in accepted_adrs
        if r.links or r.metadata.get("related") or r.source_refs
    )

    coverage: dict[str, int] = {
        "accepted_requirements_with_ac": with_ac,
        "accepted_requirements_with_implementation_refs": with_impl,
        "accepted_requirements_with_validation": with_test,
        "accepted_adrs_with_traceability": with_trace,
    }

    return SddStatusResult(profile=profile, counts=counts, coverage=coverage)


# ── helpers ─────────────────────────────────────────────────────────────


def _has_inline_acceptance_criteria(record: ArchitectureRecord) -> bool:
    ac = record.metadata.get("acceptance_criteria")
    if isinstance(ac, list) and ac:
        return True
    return False


def _has_validation(
    record: ArchitectureRecord,
    acceptance_by_requirement: dict[str, list[ArchitectureRecord]],
    records_by_id: dict[str, ArchitectureRecord],
) -> bool:
    """Check if a requirement has test/validation evidence."""
    # test_refs on the record itself
    if record.test_refs:
        return True
    # source_refs role=validates
    if any(ref.role == "validates" for ref in record.source_refs):
        return True
    # inline acceptance_criteria with validation command
    ac = record.metadata.get("acceptance_criteria")
    if isinstance(ac, list):
        for item in ac:
            if isinstance(item, dict) and item.get("validation", {}).get("command"):
                return True
    # Linked acceptance_criterion records
    for ac_record in acceptance_by_requirement.get(record.id, []):
        if ac_record.test_refs:
            return True
        if any(ref.role == "validates" for ref in ac_record.source_refs):
            return True
        v = ac_record.metadata.get("validation")
        if isinstance(v, dict) and v.get("command"):
            return True
    return False


def _qs_missing_fields(record: ArchitectureRecord) -> list[str]:
    required = (
        "quality",
        "stimulus",
        "environment",
        "artifact",
        "response",
        "response_measure",
    )
    missing = []
    for field in required:
        value = record.metadata.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append(field)
    return missing


def _looks_measurable(value: str) -> bool:
    lowered = value.lower()
    if any(char.isdigit() for char in lowered):
        return True
    indicators = (
        "%",
        "percent",
        "ms",
        "millisecond",
        "second",
        "minute",
        "hour",
        "count",
        "byte",
        "identical",
        "latency",
        "throughput",
        "less than",
        "greater than",
        "at least",
        "at most",
        "zero",
        "one",
        "two",
    )
    return any(indicator in lowered for indicator in indicators)


def _missing_reference_paths(value: object, workspace_root: Path) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    missing: list[str] = []
    for entry in value:
        if isinstance(entry, str):
            path_text = entry.partition("::")[0].strip().rstrip("/")
        elif isinstance(entry, dict):
            raw_path = entry.get("path")
            path_text = (
                raw_path.strip().rstrip("/") if isinstance(raw_path, str) else ""
            )
        else:
            continue
        if path_text and not (workspace_root / path_text).exists():
            missing.append(path_text)
    return tuple(missing)


__all__ = [
    "SddCheckResult",
    "SddFinding",
    "SddOptions",
    "SddStatusResult",
    "check_sdd",
    "check_sdd_records",
    "check_sdd_status",
]
