"""SDD (Specification-Driven Design) policy engine.

This module evaluates SDD traceability contracts on loaded records
without depending on ``cli.py``.  The CLI sub-app and test suites
call into this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from archledger.config.model import ProjectConfig

from archledger.bdd.models import DEFAULT_BDD_AUTOMATION_STATUS
from archledger.bdd.normalize import normalize_bdd_metadata
from archledger.bdd.paths import (
    deprecated_bdd_feature_path_message,
    is_deprecated_bdd_feature_path,
)
from archledger.checks import PLACEHOLDER_SNIPPETS
from archledger.model import (
    VALID_SOURCE_REF_ROLES,
    ArchitectureRecord,
)
from archledger.repository import ArchitectureRepository
from archledger.source_refs import normalize_source_refs
from archledger.test_refs import normalize_test_refs

_TASKLEDGER_ID_RE = re.compile(r"^task-\d{4,}$")

# ── data classes ────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class SddOptions:
    strict: bool = False
    require_acceptance_criteria: bool = True
    require_implementation_refs: bool = True
    require_test_refs: bool = True
    require_bdd_gwt_for_behavior_records: bool = True
    require_bdd_automation_for_accepted_records: bool = False
    include_draft: bool = False
    include_superseded: bool = False


def sdd_options_from_config(
    config: ProjectConfig,
    *,
    strict: bool,
    require_acceptance_criteria: bool | None = None,
    require_implementation_refs: bool | None = None,
    require_test_refs: bool | None = None,
    require_bdd_gwt_for_behavior_records: bool | None = None,
    require_bdd_automation_for_accepted_records: bool | None = None,
    include_draft: bool = False,
    include_superseded: bool = False,
) -> SddOptions:
    """Build the effective :class:`SddOptions` from config plus CLI overrides.

    ``config.profiles.sdd`` provides the project defaults; any non-``None```
    CLI override wins. This is the single source of truth so the enforced
    policy always matches the policy reported in JSON payloads.
    """
    sdd = config.profiles.sdd
    return SddOptions(
        strict=strict,
        require_acceptance_criteria=(
            sdd.require_acceptance_criteria
            if require_acceptance_criteria is None
            else require_acceptance_criteria
        ),
        require_implementation_refs=(
            sdd.require_implementation_refs
            if require_implementation_refs is None
            else require_implementation_refs
        ),
        require_test_refs=(
            sdd.require_test_refs if require_test_refs is None else require_test_refs
        ),
        require_bdd_gwt_for_behavior_records=(
            getattr(sdd, "require_bdd_gwt_for_behavior_records", True)
            if require_bdd_gwt_for_behavior_records is None
            else require_bdd_gwt_for_behavior_records
        ),
        require_bdd_automation_for_accepted_records=(
            getattr(sdd, "require_bdd_automation_for_accepted_records", False)
            if require_bdd_automation_for_accepted_records is None
            else require_bdd_automation_for_accepted_records
        ),
        include_draft=include_draft,
        include_superseded=include_superseded,
    )


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
    default_profile: str
    enabled_profiles: tuple[str, ...]
    sdd_enabled: bool
    policy: dict[str, bool]
    counts: dict[str, int]
    coverage: dict[str, int]


# ── public API ──────────────────────────────────────────────────────────


def check_sdd(repo: ArchitectureRepository, *, options: SddOptions) -> SddCheckResult:
    records = repo.load_all_records(include_sections=True)
    return check_sdd_records(records, repo.paths.workspace_root, options=options)


@dataclass(frozen=True, slots=True)
class SddContext:
    """Shared state for SDD rule evaluation."""

    records_by_id: dict[str, ArchitectureRecord]
    records_by_type: dict[str, list[ArchitectureRecord]]
    acceptance_by_requirement: dict[str, list[ArchitectureRecord]]
    waivers_by_record: dict[str, frozenset[str]]
    workspace_root: Path
    options: SddOptions


def _has_waiver(ctx: SddContext, record_id: str, rule: str) -> bool:
    return rule in ctx.waivers_by_record.get(record_id, frozenset())


def _build_sdd_context(
    records: list[ArchitectureRecord],
    workspace_root: Path,
    options: SddOptions,
) -> tuple[SddContext, list[SddFinding]]:
    """Build lookup tables and process waivers; return context + waiver errors."""
    errors: list[SddFinding] = []

    records_by_id = {r.id: r for r in records}
    records_by_type: dict[str, list[ArchitectureRecord]] = {}
    for r in records:
        records_by_type.setdefault(r.type, []).append(r)

    # acceptance_criterion records indexed by the requirement they validate
    acceptance_by_requirement: dict[str, list[ArchitectureRecord]] = {}
    for r in records_by_type.get("acceptance_criterion", []):
        req = r.metadata.get("requirement", "")
        if isinstance(req, str) and req.strip():
            acceptance_by_requirement.setdefault(req.strip(), []).append(r)
        for link in r.links:
            if link.rel == "validates":
                acceptance_by_requirement.setdefault(link.target, []).append(r)

    waivers_by_record: dict[str, frozenset[str]] = {}
    for r in records:
        if not options.include_draft and r.status == "draft":
            continue
        raw_waivers = r.metadata.get("sdd") or {}
        if not isinstance(raw_waivers, dict):
            raw_waivers = {}
        raw_waiver_list = raw_waivers.get("waivers", [])
        if not isinstance(raw_waiver_list, list):
            continue
        rules: set[str] = set()
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
            rules.add(rule.strip())
        if rules:
            waivers_by_record[r.id] = frozenset(rules)

    ctx = SddContext(
        records_by_id=records_by_id,
        records_by_type=records_by_type,
        acceptance_by_requirement=acceptance_by_requirement,
        waivers_by_record=waivers_by_record,
        workspace_root=workspace_root,
        options=options,
    )
    return ctx, errors


def check_sdd_records(
    records: list[ArchitectureRecord],
    workspace_root: Path,
    *,
    options: SddOptions,
) -> SddCheckResult:
    ctx, pre_errors = _build_sdd_context(records, workspace_root, options)

    findings: list[SddFinding] = list(pre_errors)
    for r in records:
        if not options.include_draft and r.status == "draft":
            continue
        if not options.include_superseded and r.status == "superseded":
            continue
        findings.extend(_check_record(r, ctx))

    errors = tuple(f for f in findings if f.level == "error")
    warnings = tuple(f for f in findings if f.level == "warning")

    summary = _build_summary(records, options)
    summary["errors"] = len(errors)
    summary["warnings"] = len(warnings)

    return SddCheckResult(errors=errors, warnings=warnings, summary=summary)


def _check_record(
    r: ArchitectureRecord,
    ctx: SddContext,
) -> list[SddFinding]:
    """Run all SDD checks for a single in-scope record."""
    findings: list[SddFinding] = []

    # SDD-PLACEHOLDER: accepted non-section records
    if r.type != "section" and r.status == "accepted":
        stripped_body = r.body.strip()
        if stripped_body and any(
            snippet in stripped_body for snippet in PLACEHOLDER_SNIPPETS
        ):
            if not _has_waiver(ctx, r.id, "SDD-PLACEHOLDER"):
                findings.append(
                    SddFinding(
                        level="error",
                        code="SDD-PLACEHOLDER",
                        message=f"Record {r.id} has placeholder body.",
                        record_id=r.id,
                        path=r.path,
                    )
                )

    # SDD-SOURCE-REF-ROLE: invalid roles
    for ref in r.source_refs:
        if ref.role and ref.role not in VALID_SOURCE_REF_ROLES:
            findings.append(
                SddFinding(
                    level="warning",
                    code="SDD-SOURCE-REF-ROLE",
                    message=f"Record {r.id} source_ref has unknown role: {ref.role!r}.",
                    record_id=r.id,
                    path=r.path,
                )
            )

    # SDD-AC-FORMAT / SDD-AC-NO-STATEMENT / SDD-AC-VALIDATION-FORMAT
    inline_ac_valid, ac_format_findings = _classify_inline_acceptance_criteria(r)
    for code, message in ac_format_findings:
        if not _has_waiver(ctx, r.id, code):
            findings.append(
                SddFinding(
                    level="error",
                    code=code,
                    message=message,
                    record_id=r.id,
                    path=r.path,
                )
            )

    # SDD-*REF-EXISTS / SDD-*REF-PATH (source + test refs)
    for code, message in _reference_findings(r, ctx.workspace_root):
        if not _has_waiver(ctx, r.id, code):
            findings.append(
                SddFinding(
                    level="error",
                    code=code,
                    message=message,
                    record_id=r.id,
                    path=r.path,
                )
            )

    # SDD-LINK-TARGET: link targets must exist (only for accepted records)
    if r.status == "accepted":
        for link in r.links:
            target = ctx.records_by_id.get(link.target)
            if target is None:
                findings.append(
                    SddFinding(
                        level="error",
                        code="SDD-LINK-TARGET",
                        message=(
                            f"Record {r.id} link target {link.target!r} does not exist."
                        ),
                        record_id=r.id,
                        path=r.path,
                    )
                )
            elif target.status in {"draft", "superseded"} and not _has_waiver(
                ctx, r.id, "SDD-LINK-TARGET-STATUS"
            ):
                findings.append(
                    SddFinding(
                        level="warning",
                        code="SDD-LINK-TARGET-STATUS",
                        message=(
                            f"Record {r.id} links to "
                            f"{link.target!r} which is {target.status}."
                        ),
                        record_id=r.id,
                        path=r.path,
                    )
                )

    # Type-specific checks
    if r.type == "requirement" and r.status == "accepted":
        findings.extend(_check_requirement(r, ctx, inline_ac_valid))
    elif r.type == "adr" and r.status == "accepted":
        findings.extend(_check_adr(r, ctx))
    elif r.type == "quality_scenario" and r.status == "accepted":
        findings.extend(_check_quality_scenario(r, ctx))

    # BDD-specific checks (all accepted records that carry bdd metadata)
    if r.status == "accepted" and r.metadata.get("bdd") is not None:
        findings.extend(_check_bdd(r, ctx))

    if r.status == "accepted":
        findings.extend(_check_taskledger_provenance(r, ctx))

    return findings


def _check_taskledger_provenance(
    r: ArchitectureRecord,
    ctx: SddContext,
 ) -> list[SddFinding]:
    findings: list[SddFinding] = []
    values = _taskledger_ids(r.metadata)
    for value in values:
        if not _TASKLEDGER_ID_RE.match(value) and not _has_waiver(
            ctx, r.id, "SDD-TASKLEDGER-ID-SHAPE"
        ):
            findings.append(
                SddFinding(
                    level="error",
                    code="SDD-TASKLEDGER-ID-SHAPE",
                    message=(
                        f"Record {r.id} has Taskledger provenance id {value!r}; "
                        "expected task-NNNN shape."
                    ),
                    record_id=r.id,
                    path=r.path,
                )
            )
    return findings


def _taskledger_ids(value: object) -> list[str]:
    ids: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in {
                "task_id",
                "taskledger_id",
                "task_ids",
                "taskledger_ids",
            }:
                ids.extend(_taskledger_ids(item))
            elif lowered in {"links", "related"}:
                ids.extend(_taskledger_link_ids(item))
    elif isinstance(value, list):
        for item in value:
            ids.extend(_taskledger_ids(item))
    elif isinstance(value, str):
        ids.append(value)
    return ids


def _taskledger_link_ids(value: object) -> list[str]:
    if isinstance(value, dict):
        return [
            found
            for item in value.values()
            for found in _taskledger_link_ids(item)
        ]
    if isinstance(value, list):
        return [found for item in value for found in _taskledger_link_ids(item)]
    if isinstance(value, str) and "task" in value.lower():
        return [value]
    return []


def _check_requirement(
    r: ArchitectureRecord,
    ctx: SddContext,
    inline_ac_valid: list[dict[str, object]],
) -> list[SddFinding]:
    """SDD-REQ-AC, SDD-REQ-IMPL, SDD-REQ-TEST checks."""
    findings: list[SddFinding] = []

    if ctx.options.require_acceptance_criteria and not _has_waiver(
        ctx, r.id, "SDD-REQ-AC"
    ):
        if not (inline_ac_valid or r.id in ctx.acceptance_by_requirement):
            findings.append(
                SddFinding(
                    level="error",
                    code="SDD-REQ-AC",
                    message=f"Accepted requirement {r.id} has no acceptance criteria.",
                    record_id=r.id,
                    path=r.path,
                )
            )

    if ctx.options.require_implementation_refs and not _has_waiver(
        ctx, r.id, "SDD-REQ-IMPL"
    ):
        if not any(ref.role == "implements" for ref in r.source_refs):
            findings.append(
                SddFinding(
                    level="error",
                    code="SDD-REQ-IMPL",
                    message=(
                        f"Accepted requirement {r.id} has no "
                        "implementation source_refs."
                    ),
                    record_id=r.id,
                    path=r.path,
                )
            )

    if ctx.options.require_test_refs and not _has_waiver(ctx, r.id, "SDD-REQ-TEST"):
        if not _has_validation(r, ctx.acceptance_by_requirement, ctx.records_by_id):
            findings.append(
                SddFinding(
                    level="error",
                    code="SDD-REQ-TEST",
                    message=f"Accepted requirement {r.id} has no validation.",
                    record_id=r.id,
                    path=r.path,
                )
            )

    return findings


def _check_adr(r: ArchitectureRecord, ctx: SddContext) -> list[SddFinding]:
    """SDD-ADR-LINK traceability check."""
    if _has_waiver(ctx, r.id, "SDD-ADR-LINK"):
        return []
    has_traceability = (
        bool(r.links) or bool(r.metadata.get("related")) or bool(r.source_refs)
    )
    if has_traceability:
        return []
    return [
        SddFinding(
            level="error",
            code="SDD-ADR-LINK",
            message=f"Accepted ADR {r.id} has no traceability.",
            record_id=r.id,
            path=r.path,
        )
    ]


def _check_quality_scenario(
    r: ArchitectureRecord,
    ctx: SddContext,
) -> list[SddFinding]:
    """SDD-QS-COMPLETE and SDD-QS-MEASURABLE checks."""
    findings: list[SddFinding] = []

    if not _has_waiver(ctx, r.id, "SDD-QS-COMPLETE"):
        missing = _qs_missing_fields(r)
        if missing:
            findings.append(
                SddFinding(
                    level="error",
                    code="SDD-QS-COMPLETE",
                    message=(
                        f"Accepted quality_scenario {r.id} "
                        f"is missing: {', '.join(missing)}."
                    ),
                    record_id=r.id,
                    path=r.path,
                )
            )

    if not _has_waiver(ctx, r.id, "SDD-QS-MEASURABLE"):
        resp_measure = r.metadata.get("response_measure", "")
        if isinstance(resp_measure, str) and resp_measure.strip():
            if not _looks_measurable(resp_measure):
                findings.append(
                    SddFinding(
                        level="warning",
                        code="SDD-QS-MEASURABLE",
                        message=(
                            f"Quality_scenario {r.id} response_measure"
                            " is not measurable."
                        ),
                        record_id=r.id,
                        path=r.path,
                    )
                )

    return findings


def _build_summary(
    records: list[ArchitectureRecord],
    options: SddOptions,
) -> dict[str, int]:
    """Build the summary dict (errors/warnings counts are added by the caller)."""
    in_scope_records = [
        r
        for r in records
        if (options.include_draft or r.status != "draft")
        and (options.include_superseded or r.status != "superseded")
    ]
    return {
        "records_total": len(records),
        "records_checked": len(in_scope_records),
        "accepted_requirements": len(
            [r for r in records if r.type == "requirement" and r.status == "accepted"]
        ),
        "acceptance_criteria": len(
            [r for r in records if r.type == "acceptance_criterion"]
        ),
    }


def check_sdd_status(repo: ArchitectureRepository) -> SddStatusResult:
    config = repo.config
    enabled_profiles = tuple(config.profiles.profiles.enabled)
    default_profile = config.profiles.profiles.default
    sdd_enabled = "sdd" in enabled_profiles
    options = sdd_options_from_config(config, strict=False)
    policy = {
        "require_acceptance_criteria": options.require_acceptance_criteria,
        "require_implementation_refs": options.require_implementation_refs,
        "require_test_refs": options.require_test_refs,
        "require_bdd_gwt_for_behavior_records": (
            options.require_bdd_gwt_for_behavior_records
        ),
        "require_bdd_automation_for_accepted_records": (
            options.require_bdd_automation_for_accepted_records
        ),
    }
    records = repo.load_all_records(include_sections=True)

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

    return SddStatusResult(
        default_profile=default_profile,
        enabled_profiles=enabled_profiles,
        sdd_enabled=sdd_enabled,
        policy=policy,
        counts=counts,
        coverage=coverage,
    )


# ── SDD coverage ─────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class SddCoverageDimension:
    covered: int = 0
    total: int = 0


@dataclass(frozen=True, slots=True)
class SddCoverageResult:
    default_profile: str
    enabled_profiles: tuple[str, ...]
    sdd_enabled: bool
    totals: dict[str, int]
    coverage: dict[str, SddCoverageDimension]
    gaps: tuple[str, ...]
    by_record: tuple[dict[str, object], ...] = ()


def check_sdd_coverage(
    repo: ArchitectureRepository,
    *,
    include_bdd: bool = False,
    by_record: bool = False,
) -> SddCoverageResult:
    config = repo.config
    records = repo.load_all_records(include_sections=True)
    enabled_profiles = tuple(config.profiles.profiles.enabled)
    default_profile = config.profiles.profiles.default
    sdd_enabled = "sdd" in enabled_profiles

    acceptance_by_req: dict[str, list[ArchitectureRecord]] = {}
    for r in records:
        if r.type == "acceptance_criterion":
            req = r.metadata.get("requirement", "")
            if isinstance(req, str) and req.strip():
                acceptance_by_req.setdefault(req.strip(), []).append(r)
            for link in r.links:
                if link.rel == "validates":
                    acceptance_by_req.setdefault(link.target, []).append(r)

    accepted_reqs = [
        r for r in records if r.type == "requirement" and r.status == "accepted"
    ]
    accepted_adrs = [r for r in records if r.type == "adr" and r.status == "accepted"]
    all_risks = [r for r in records if r.type == "risk"]
    behavior_records = [
        r
        for r in records
        if r.type in ("runtime_scenario", "quality_scenario") and r.status == "accepted"
    ]

    reqs_with_ac = sum(
        1
        for r in accepted_reqs
        if _has_inline_acceptance_criteria(r) or r.id in acceptance_by_req
    )
    reqs_with_impl = sum(
        1
        for r in accepted_reqs
        if any(ref.role == "implements" for ref in r.source_refs)
    )
    reqs_with_validation = sum(
        1
        for r in accepted_reqs
        if _has_validation(r, acceptance_by_req, {r.id: r for r in records})
    )
    adrs_with_trace = sum(
        1
        for r in accepted_adrs
        if r.links or r.metadata.get("related") or r.source_refs
    )
    risks_linked = sum(
        1
        for r in all_risks
        if r.links
        or any(
            ref.role in ("implements", "validates", "documents")
            for ref in r.source_refs
        )
    )

    def _dim(c: int, t: int) -> SddCoverageDimension:
        return SddCoverageDimension(covered=c, total=t)

    cov: dict[str, SddCoverageDimension] = {
        "accepted_requirements_with_ac": _dim(reqs_with_ac, len(accepted_reqs)),
        "accepted_requirements_with_implementation_refs": _dim(
            reqs_with_impl, len(accepted_reqs)
        ),
        "accepted_requirements_with_validation": _dim(
            reqs_with_validation, len(accepted_reqs)
        ),
        "accepted_adrs_with_traceability": _dim(adrs_with_trace, len(accepted_adrs)),
        "risks_linked": _dim(risks_linked, len(all_risks)),
    }

    if include_bdd:
        cov.update(_count_bdd_coverage(behavior_records))

    gaps: list[str] = []
    if reqs_with_ac < len(accepted_reqs):
        gaps.append(
            f"{len(accepted_reqs) - reqs_with_ac} accepted requirement(s) missing AC."
        )
    if reqs_with_impl < len(accepted_reqs):
        gaps.append(
            f"{len(accepted_reqs) - reqs_with_impl} accepted requirement(s)"
            " missing implementation refs."
        )
    if reqs_with_validation < len(accepted_reqs):
        gaps.append(
            f"{len(accepted_reqs) - reqs_with_validation} accepted requirement(s)"
            " missing validation."
        )
    if adrs_with_trace < len(accepted_adrs):
        gaps.append(
            f"{len(accepted_adrs) - adrs_with_trace} accepted ADR(s)"
            " missing traceability."
        )

    # Per-record detail (only when requested). Mirrors the aggregate counters
    # so each accepted requirement/ADR/behavior record lists its covered flags
    # and the gaps that keep it from full coverage.
    by_record_rows = (
        _coverage_record_rows(records, acceptance_by_req) if by_record else []
    )

    return SddCoverageResult(
        default_profile=default_profile,
        enabled_profiles=enabled_profiles,
        sdd_enabled=sdd_enabled,
        totals={
            "accepted_requirements": len(accepted_reqs),
            "accepted_adrs": len(accepted_adrs),
            "behavior_records": len(behavior_records),
            "risks": len(all_risks),
        },
        coverage=cov,
        gaps=tuple(gaps),
        by_record=tuple(by_record_rows),
    )


def _count_bdd_coverage(
    behavior_records: list[ArchitectureRecord],
) -> dict[str, SddCoverageDimension]:
    """Count BDD coverage dimensions for accepted behavior records."""
    behavior_with_gwt = 0
    behavior_with_feature = 0
    behavior_linked = 0
    behavior_automated = 0
    for br in behavior_records:
        raw_bdd = br.metadata.get("bdd")
        if raw_bdd is None:
            continue
        example, _warnings = normalize_bdd_metadata(br.id, raw_bdd)
        if example is None:
            continue
        if example.given and example.when and example.then:
            behavior_with_gwt += 1
        auto = example.automation
        auto_status = auto.status if auto else DEFAULT_BDD_AUTOMATION_STATUS
        if auto and auto.feature_file:
            behavior_with_feature += 1
        if auto_status == "linked":
            behavior_linked += 1
        if auto_status == "automated":
            behavior_automated += 1
    total = len(behavior_records)
    return {
        "behavior_with_gwt": SddCoverageDimension(
            covered=behavior_with_gwt, total=total
        ),
        "behavior_with_feature_file": SddCoverageDimension(
            covered=behavior_with_feature, total=total
        ),
        "behavior_linked": SddCoverageDimension(covered=behavior_linked, total=total),
        "behavior_automated": SddCoverageDimension(
            covered=behavior_automated, total=total
        ),
    }


def _coverage_record_rows(
    records: list[ArchitectureRecord],
    acceptance_by_req: dict[str, list[ArchitectureRecord]],
) -> list[dict[str, object]]:
    """Per-record coverage detail for accepted requirements/ADRs/behavior."""
    records_by_id = {r.id: r for r in records}
    rows: list[dict[str, object]] = []
    for r in records:
        if r.status != "accepted":
            continue
        if r.type == "requirement":
            has_ac = _has_inline_acceptance_criteria(r) or r.id in acceptance_by_req
            has_impl = any(ref.role == "implements" for ref in r.source_refs)
            has_val = _has_validation(r, acceptance_by_req, records_by_id)
            rec_gaps = [
                name
                for present, name in [
                    (has_ac, "acceptance_criteria"),
                    (has_impl, "implementation_refs"),
                    (has_val, "validation"),
                ]
                if not present
            ]
            rows.append(
                {
                    "record_id": r.id,
                    "type": r.type,
                    "status": r.status,
                    "covered": {
                        "acceptance_criteria": has_ac,
                        "implementation_refs": has_impl,
                        "validation": has_val,
                    },
                    "gaps": rec_gaps,
                }
            )
        elif r.type == "adr":
            has_trace = bool(r.links or r.metadata.get("related") or r.source_refs)
            rows.append(
                {
                    "record_id": r.id,
                    "type": r.type,
                    "status": r.status,
                    "covered": {"traceability": has_trace},
                    "gaps": [] if has_trace else ["traceability"],
                }
            )
        elif r.type in ("runtime_scenario", "quality_scenario"):
            rows.append(_coverage_behavior_row(r))
    return rows


def _coverage_behavior_row(record: ArchitectureRecord) -> dict[str, object]:
    """Coverage row for a runtime/quality scenario with optional bdd metadata."""
    raw_bdd = record.metadata.get("bdd")
    covered: dict[str, object] = {
        "gwt": False,
        "feature_file": False,
        "automation": False,
    }
    rec_gaps: list[str] = ["bdd_metadata"]
    if isinstance(raw_bdd, dict):
        example, _w = normalize_bdd_metadata(record.id, raw_bdd)
        if example is not None:
            gwt = bool(example.given and example.when and example.then)
            auto = example.automation
            auto_status = auto.status if auto else DEFAULT_BDD_AUTOMATION_STATUS
            covered = {
                "gwt": gwt,
                "feature_file": bool(auto and auto.feature_file),
                "automation": auto_status == "automated",
            }
            rec_gaps = [
                name
                for present, name in [
                    (gwt, "gwt"),
                    (bool(auto and auto.feature_file), "feature_file"),
                    (auto_status == "automated", "automation"),
                ]
                if not present
            ]
    return {
        "record_id": record.id,
        "type": record.type,
        "status": record.status,
        "covered": covered,
        "gaps": rec_gaps,
    }


# ── helpers ─────────────────────────────────────────────────────────────


def _classify_inline_acceptance_criteria(
    record: ArchitectureRecord,
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    """Split inline ``acceptance_criteria`` into valid items and findings.

    A valid inline criterion is a mapping with a non-empty ``statement``.
    Malformed entries produce ``(code, message)`` findings the caller maps to
    SDD errors. ``validation`` is optional but, when present, must be a mapping
    (otherwise an ``SDD-AC-VALIDATION-FORMAT`` finding is emitted while the
    criterion still counts as present).
    """
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


def _valid_inline_acceptance_criteria(
    record: ArchitectureRecord,
) -> list[dict[str, object]]:
    return _classify_inline_acceptance_criteria(record)[0]


def _has_inline_acceptance_criteria(record: ArchitectureRecord) -> bool:
    return bool(_valid_inline_acceptance_criteria(record))


def _has_validation(
    record: ArchitectureRecord,
    acceptance_by_requirement: dict[str, list[ArchitectureRecord]],
    records_by_id: dict[str, ArchitectureRecord],
) -> bool:
    """Check if a requirement has test/validation evidence."""
    del records_by_id  # retained for API compatibility
    # test_refs on the record itself
    if record.test_refs:
        return True
    # source_refs role=validates
    if any(ref.role == "validates" for ref in record.source_refs):
        return True
    # inline acceptance_criteria with a validation command
    for item in _valid_inline_acceptance_criteria(record):
        validation = item.get("validation")
        if isinstance(validation, dict) and validation.get("command"):
            return True
    # Linked acceptance_criterion records
    for ac_record in acceptance_by_requirement.get(record.id, []):
        if ac_record.test_refs:
            return True
        if any(ref.role == "validates" for ref in ac_record.source_refs):
            return True
        validation = ac_record.metadata.get("validation")
        if isinstance(validation, dict) and validation.get("command"):
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


def _reference_findings(
    record: ArchitectureRecord,
    workspace_root: Path,
) -> list[tuple[str, str]]:
    """Re-normalize raw source/test refs and map warnings to SDD findings.

    The repository loader drops missing ``source_ref`` entries at load time,
    so existence/format problems can only be detected by re-normalizing the
    raw metadata here. Role checks keep using the already-normalized
    ``record.source_refs``/``record.test_refs``.
    """
    findings: list[tuple[str, str]] = []
    raw_source = record.metadata.get("source_refs")
    if raw_source is not None:
        _refs, warnings = normalize_source_refs(
            record.id, raw_source, workspace_root=workspace_root
        )
        findings.extend(
            (
                "SDD-SOURCE-REF-EXISTS"
                if "does not exist" in warning
                else "SDD-SOURCE-REF-PATH",
                warning,
            )
            for warning in warnings
        )
    raw_test = record.metadata.get("test_refs")
    if raw_test is not None:
        _test_refs, warnings = normalize_test_refs(
            record.id, raw_test, workspace_root=workspace_root
        )
        findings.extend(
            (
                "SDD-TEST-REF-EXISTS"
                if "does not exist" in warning
                else "SDD-TEST-REF-PATH",
                warning,
            )
            for warning in warnings
        )
    return findings


def _check_bdd(
    r: ArchitectureRecord,
    ctx: SddContext,
) -> list[SddFinding]:
    """Run BDD-specific SDD checks for an accepted record with bdd metadata.

    Checks:
    * SDD-BDD-SHAPE: bdd block must be structurally valid (warning from normalizer
      is promoted to error).
    * SDD-BDD-GWT: accepted runtime_scenario with bdd must have non-empty given,
      when, and then.
    * SDD-BDD-AUTOMATION: warn on pending automation unless the profile requires it.
    * SDD-BDD-FEATURE-REF: feature_file must be linked via source_refs role=documents.
    * SDD-BDD-TEST-REF: automated behavior should link executable pytest tests.
    * SDD-BDD-FEATURE-PATH-CONVENTION: deprecated feature file locations warn.
    * SDD-BDD-AC-LINK: referenced AC IDs should exist.
    """
    findings: list[SddFinding] = []
    raw_bdd = r.metadata.get("bdd")

    # SDD-BDD-SHAPE: normalize and promote warnings to errors
    example, shape_warnings = normalize_bdd_metadata(r.id, raw_bdd)
    if example is None and shape_warnings:
        findings.append(
            SddFinding(
                level="error",
                code="SDD-BDD-SHAPE",
                message=(
                    f"Record {r.id} bdd metadata is structurally invalid: "
                    + "; ".join(shape_warnings)
                ),
                record_id=r.id,
                path=r.path,
            )
        )
        return findings  # can't run further checks without a valid example

    if shape_warnings and example is not None:
        # Promote normalizer warnings to errors for accepted records
        for warning in shape_warnings:
            findings.append(
                SddFinding(
                    level="error",
                    code="SDD-BDD-SHAPE",
                    message=warning,
                    record_id=r.id,
                    path=r.path,
                )
            )

    if example is None:
        return findings

    # SDD-BDD-GWT: required for accepted behavior records (runtime and quality
    # scenarios) that carry bdd metadata.
    if r.type in ("runtime_scenario", "quality_scenario"):
        _require_gwt = ctx.options.require_bdd_gwt_for_behavior_records
        if _require_gwt and not _has_waiver(ctx, r.id, "SDD-BDD-GWT"):
            missing = [
                name
                for step, name in [
                    (example.given, "given"),
                    (example.when, "when"),
                    (example.then, "then"),
                ]
                if not step
            ]
            if missing:
                findings.append(
                    SddFinding(
                        level="error",
                        code="SDD-BDD-GWT",
                        message=(
                            f"Accepted {r.type} {r.id} bdd metadata is "
                            f"missing: {', '.join(missing)}."
                        ),
                        record_id=r.id,
                        path=r.path,
                    )
                )

    # SDD-BDD-AUTOMATION: under strict policy only automated / not_applicable
    # satisfy the requirement; pending and linked are failing. Under the lenient
    # default, pending is a warning and linked is acceptable (feature file
    # present, runner not yet wired).
    if example.automation is not None:
        auto_status = example.automation.status
    else:
        auto_status = DEFAULT_BDD_AUTOMATION_STATUS
    require_automation = ctx.options.require_bdd_automation_for_accepted_records
    not_satisfied = auto_status in ("pending", "linked")
    if (
        not_satisfied
        and require_automation
        and not _has_waiver(ctx, r.id, "SDD-BDD-AUTOMATION")
    ):
        findings.append(
            SddFinding(
                level="error",
                code="SDD-BDD-AUTOMATION",
                message=(
                    f"Record {r.id} has bdd with automation.status={auto_status};"
                    " automation is required by profile policy"
                    " (reach status automated or not_applicable, or waive the rule)."
                ),
                record_id=r.id,
                path=r.path,
            )
        )
    elif (
        auto_status == "pending"
        and not require_automation
        and not _has_waiver(ctx, r.id, "SDD-BDD-AUTOMATION")
    ):
        findings.append(
            SddFinding(
                level="warning",
                code="SDD-BDD-AUTOMATION",
                message=(
                    f"Record {r.id} has bdd with automation.status=pending; "
                    "link to a feature file when automation is wired."
                ),
                record_id=r.id,
                path=r.path,
            )
        )

    if (
        auto_status == "linked"
        and not r.test_refs
        and not _has_waiver(ctx, r.id, "SDD-BDD-AUTOMATION-REF")
    ):
        findings.append(
            SddFinding(
                level="error",
                code="SDD-BDD-AUTOMATION-REF",
                message=(
                    f"Record {r.id} has bdd with automation.status=linked but "
                    "no executable test_refs are recorded; add a pytest test_ref, "
                    "use automation.status=not_applicable for manual validation, "
                    "or waive the rule."
                ),
                record_id=r.id,
                path=r.path,
            )
        )

    # SDD-BDD-FEATURE-REF: feature_file must be linked via source_refs role=documents
    if (
        example.automation is not None
        and example.automation.feature_file
        and not _has_waiver(ctx, r.id, "SDD-BDD-FEATURE-REF")
    ):
        feat_path = example.automation.feature_file
        is_linked = any(
            ref.path == feat_path and ref.role == "documents" for ref in r.source_refs
        )
        if not is_linked:
            findings.append(
                SddFinding(
                    level="error",
                    code="SDD-BDD-FEATURE-REF",
                    message=(
                        f"Record {r.id} bdd.automation.feature_file "
                        f"{feat_path!r} is not linked via source_refs with role "
                        "'documents'."
                    ),
                    record_id=r.id,
                    path=r.path,
                )
            )
        if is_deprecated_bdd_feature_path(feat_path) and not _has_waiver(
            ctx, r.id, "SDD-BDD-FEATURE-PATH-CONVENTION"
        ):
            findings.append(
                SddFinding(
                    level="warning",
                    code="SDD-BDD-FEATURE-PATH-CONVENTION",
                    message=(
                        f"Record {r.id} bdd.automation.feature_file "
                        + deprecated_bdd_feature_path_message(feat_path)
                    ),
                    record_id=r.id,
                    path=r.path,
                )
            )

    if (
        auto_status == "automated"
        and not r.test_refs
        and not _has_waiver(ctx, r.id, "SDD-BDD-TEST-REF")
    ):
        findings.append(
            SddFinding(
                level="error" if require_automation else "warning",
                code="SDD-BDD-TEST-REF",
                message=(
                    f"Record {r.id} has bdd with automation.status=automated but "
                    "no executable test_refs are recorded."
                ),
                record_id=r.id,
                path=r.path,
            )
        )

    # SDD-BDD-AC-LINK: referenced AC IDs should exist
    if example.acceptance_criteria and not _has_waiver(ctx, r.id, "SDD-BDD-AC-LINK"):
        for ac_id in example.acceptance_criteria:
            if ac_id not in ctx.records_by_id:
                findings.append(
                    SddFinding(
                        level="warning",
                        code="SDD-BDD-AC-LINK",
                        message=(
                            f"Record {r.id} bdd.acceptance_criteria "
                            f"references {ac_id!r} which does not exist."
                        ),
                        record_id=r.id,
                        path=r.path,
                    )
                )

    return findings


__all__ = [
    "SddCheckResult",
    "SddContext",
    "SddFinding",
    "SddOptions",
    "SddStatusResult",
    "check_sdd",
    "check_sdd_records",
    "check_sdd_status",
    "sdd_options_from_config",
]
