"""Static registry of SDD rule codes.

This is the single source of truth for the SDD rule codes emitted by
:mod:`archledger.sdd`. It powers ``archledger sdd explain`` and rule-code
validation for ``archledger sdd waive``.

Each entry records:

* ``code``       — the stable rule id (e.g. ``SDD-REQ-AC``)
* ``severity``   — the default severity and how policy affects it
* ``meaning``    — one-line description of what the rule checks
* ``fix``        — actionable guidance to resolve a finding
* ``waivable``   — whether ``sdd.waivers[]`` can suppress this rule
* ``waiver_example`` — a front-matter snippet showing a valid waiver

Keeping the registry here (rather than scattered strings in ``sdd.py``) means
documentation, explain output, and waive validation never drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SddRuleInfo:
    """Human- and machine-readable metadata for one SDD rule code."""

    code: str
    severity: str
    meaning: str
    fix: str
    waivable: bool
    waiver_example: str = ""


def _waiver(code: str, reason: str) -> str:
    return f"sdd:\n  waivers:\n    - rule: {code}\n      reason: {reason}"


_SDD_RULES: tuple[SddRuleInfo, ...] = (
    SddRuleInfo(
        code="SDD-PLACEHOLDER",
        severity="error",
        meaning="Accepted non-section record still contains "
        "a template placeholder body.",
        fix="Replace the placeholder body with real content "
        "(record body set, or edit the record).",
        waivable=True,
        waiver_example=_waiver(
            "SDD-PLACEHOLDER", "Legacy record, body authored externally."
        ),
    ),
    SddRuleInfo(
        code="SDD-SOURCE-REF-ROLE",
        severity="warning",
        meaning="A source_ref uses a role outside the allowed set.",
        fix="Use one of the valid source_ref roles "
        "(e.g. implements, validates, documents).",
        waivable=True,
        waiver_example=_waiver(
            "SDD-SOURCE-REF-ROLE", "Custom role kept for legacy tooling."
        ),
    ),
    SddRuleInfo(
        code="SDD-AC-FORMAT",
        severity="error",
        meaning="An inline acceptance_criteria entry is not a mapping.",
        fix="Make each acceptance_criteria entry a mapping with a 'statement' field.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-AC-FORMAT", "Imported AC shape kept for traceability."
        ),
    ),
    SddRuleInfo(
        code="SDD-AC-NO-STATEMENT",
        severity="error",
        meaning="An inline acceptance_criteria entry has no statement.",
        fix="Add a non-empty 'statement' string to the acceptance_criteria entry.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-AC-NO-STATEMENT", "Statement lives in linked AC record."
        ),
    ),
    SddRuleInfo(
        code="SDD-AC-VALIDATION-FORMAT",
        severity="error",
        meaning="An acceptance_criteria validation field is not a mapping.",
        fix="Make 'validation' a mapping (e.g. {command: ..., expected: passes}).",
        waivable=True,
        waiver_example=_waiver("SDD-AC-VALIDATION-FORMAT", "Manual validation only."),
    ),
    SddRuleInfo(
        code="SDD-SOURCE-REF-EXISTS",
        severity="error",
        meaning="A source_ref points at a file that does not exist in the workspace.",
        fix="Create the referenced file or remove/fix the source_ref path.",
        waivable=True,
        waiver_example=_waiver("SDD-SOURCE-REF-EXISTS", "Generated at build time."),
    ),
    SddRuleInfo(
        code="SDD-SOURCE-REF-PATH",
        severity="error",
        meaning="A source_ref path is not a safe relative POSIX path.",
        fix="Use a workspace-relative POSIX path with no '..' or backslashes.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-SOURCE-REF-PATH", "Absolute path kept for monorepo tooling."
        ),
    ),
    SddRuleInfo(
        code="SDD-TEST-REF-EXISTS",
        severity="error",
        meaning="A test_ref points at a file that does not exist in the workspace.",
        fix="Create the referenced test or remove/fix the test_ref path.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-TEST-REF-EXISTS", "Tests live in a separate package."
        ),
    ),
    SddRuleInfo(
        code="SDD-TEST-REF-PATH",
        severity="error",
        meaning="A test_ref path is not a safe relative POSIX path.",
        fix="Use a workspace-relative POSIX path with no '..' or backslashes.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-TEST-REF-PATH", "Absolute path kept for monorepo tooling."
        ),
    ),
    SddRuleInfo(
        code="SDD-LINK-TARGET",
        severity="error",
        meaning="An accepted record links to a target id that does not exist.",
        fix="Create the target record or correct the link target id.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-LINK-TARGET", "Target record lives in another ledger."
        ),
    ),
    SddRuleInfo(
        code="SDD-LINK-TARGET-STATUS",
        severity="warning",
        meaning="An accepted record links to a draft or superseded record.",
        fix="Accept the target record, supersede the link, or waive if intentional.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-LINK-TARGET-STATUS", "Draft target is expected during rollout."
        ),
    ),
    SddRuleInfo(
        code="SDD-REQ-AC",
        severity="error",
        meaning="Accepted requirement has no acceptance criteria "
        "(inline or linked AC record).",
        fix="Add inline acceptance_criteria or link an acceptance_criterion record.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-REQ-AC", "Legacy requirement accepted before AC policy."
        ),
    ),
    SddRuleInfo(
        code="SDD-REQ-IMPL",
        severity="error",
        meaning="Accepted requirement has no implementation source_refs.",
        fix="Add a source_ref with role 'implements' pointing at the implementation.",
        waivable=True,
        waiver_example=_waiver("SDD-REQ-IMPL", "Implemented in a vendored module."),
    ),
    SddRuleInfo(
        code="SDD-REQ-TEST",
        severity="error",
        meaning="Accepted requirement has no validation/test evidence.",
        fix="Add a test_ref, a source_ref role 'validates', "
        "or a validation command on an AC.",
        waivable=True,
        waiver_example=_waiver("SDD-REQ-TEST", "Validated by an external test suite."),
    ),
    SddRuleInfo(
        code="SDD-ADR-LINK",
        severity="error",
        meaning="Accepted ADR has no traceability (links, related, or source_refs).",
        fix="Add a link, a related entry, or a source_ref to the ADR.",
        waivable=True,
        waiver_example=_waiver("SDD-ADR-LINK", "Standalone decision record."),
    ),
    SddRuleInfo(
        code="SDD-QS-COMPLETE",
        severity="error",
        meaning="Accepted quality_scenario is missing required fields.",
        fix="Fill in quality, stimulus, environment, artifact, "
        "response, response_measure.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-QS-COMPLETE", "Partial scenario kept for roadmap tracking."
        ),
    ),
    SddRuleInfo(
        code="SDD-QS-MEASURABLE",
        severity="warning",
        meaning="quality_scenario response_measure does not look measurable.",
        fix="Add a numeric or comparator-based target (e.g. '< 200 ms', '99.9%').",
        waivable=True,
        waiver_example=_waiver("SDD-QS-MEASURABLE", "Qualitative target by design."),
    ),
    SddRuleInfo(
        code="SDD-BDD-SHAPE",
        severity="error",
        meaning="Accepted record has structurally invalid bdd metadata.",
        fix="Correct the bdd block shape "
        "(feature/scenario/given/when/then/automation).",
        waivable=True,
        waiver_example=_waiver("SDD-BDD-SHAPE", "Custom bdd shape kept for migration."),
    ),
    SddRuleInfo(
        code="SDD-BDD-GWT",
        severity="error",
        meaning="Accepted runtime_scenario with bdd is missing given/when/then steps.",
        fix="Populate non-empty given/when/then in the bdd block "
        "(or disable the policy).",
        waivable=True,
        waiver_example=_waiver("SDD-BDD-GWT", "GWT captured in linked feature file."),
    ),
    SddRuleInfo(
        code="SDD-BDD-AUTOMATION",
        severity="warning by default, error when "
        "require_bdd_automation_for_accepted_records=true",
        meaning="Accepted record has bdd with automation.status=pending.",
        fix="Set automation.status to linked/automated and add feature_file/test refs.",
        waivable=True,
        waiver_example=_waiver("SDD-BDD-AUTOMATION", "Manual verification only."),
    ),
    SddRuleInfo(
        code="SDD-BDD-FEATURE-REF",
        severity="error",
        meaning="bdd.automation.feature_file is not linked "
        "via source_refs or test_refs.",
        fix="Add a source_ref (role documents) or test_ref for the feature file path.",
        waivable=True,
        waiver_example=_waiver(
            "SDD-BDD-FEATURE-REF", "Feature file lives outside the workspace."
        ),
    ),
    SddRuleInfo(
        code="SDD-BDD-AC-LINK",
        severity="warning",
        meaning="bdd.acceptance_criteria references an AC id that does not exist.",
        fix="Create the referenced acceptance_criterion record or fix the id.",
        waivable=True,
        waiver_example=_waiver("SDD-BDD-AC-LINK", "AC record lives in another ledger."),
    ),
    SddRuleInfo(
        code="SDD-WAIVER-NO-REASON",
        severity="error",
        meaning="A waiver entry has no reason.",
        fix="Add a non-empty 'reason' to the waiver entry.",
        waivable=False,
    ),
)

_RULES_BY_CODE: dict[str, SddRuleInfo] = {info.code: info for info in _SDD_RULES}


def all_sdd_rules() -> tuple[SddRuleInfo, ...]:
    """Return every registered SDD rule, in registry order."""
    return _SDD_RULES


def get_sdd_rule(code: str) -> SddRuleInfo | None:
    """Return the rule info for *code*, or ``None`` if unknown."""
    return _RULES_BY_CODE.get(code)


def is_known_sdd_rule(code: str) -> bool:
    """Return ``True`` if *code* is a registered SDD rule code."""
    return code in _RULES_BY_CODE


def known_sdd_rule_codes() -> tuple[str, ...]:
    """Return the sorted tuple of all registered SDD rule codes."""
    return tuple(sorted(_RULES_BY_CODE))


__all__ = [
    "SddRuleInfo",
    "all_sdd_rules",
    "get_sdd_rule",
    "is_known_sdd_rule",
    "known_sdd_rule_codes",
]
