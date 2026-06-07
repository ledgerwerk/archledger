"""Immutable dataclasses describing normalized BDD behavior metadata.

These mirror the canonical ``bdd`` front-matter block documented in
``archledger_bdd_cucumber_agent_brief.md``.  They are deliberately decoupled
from any Cucumber/``pytest-bdd`` runtime: archledger stores Discovery and
Formulation metadata plus an *optional* automation pointer it never executes.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Allowed values for ``bdd.automation.status``.
#: ``pending``    — no automation yet (Discovery/Formulation value).
#: ``linked``     — a feature file / scenario is linked but not yet wired.
#: ``automated``  — an automation command is recorded and runs externally.
#: ``not_applicable`` — behavior intentionally has no automation.
BDD_AUTOMATION_STATUSES: frozenset[str] = frozenset(
    {"pending", "linked", "automated", "not_applicable"}
)

#: Default automation status when a block is imported without one.
DEFAULT_BDD_AUTOMATION_STATUS = "pending"


@dataclass(frozen=True, slots=True)
class BddAutomation:
    """Optional automation pointer for a BDD example.

    archledger stores these fields for traceability only; ``command`` is
    **never executed** by archledger.  ``feature_file``, when present, is a
    safe relative POSIX path (validated by the normalizer).
    """

    status: str = DEFAULT_BDD_AUTOMATION_STATUS
    feature_file: str = ""
    scenario: str = ""
    command: str = ""


@dataclass(frozen=True, slots=True)
class BddExample:
    """A normalized BDD behavioral example.

    Fields map one-to-one onto the canonical ``bdd`` front-matter block.
    Sequence fields are tuples so the dataclass is hashable and immutable.
    """

    feature: str
    rule: str
    scenario: str
    given: tuple[str, ...]
    when: tuple[str, ...]
    then: tuple[str, ...]
    tags: tuple[str, ...] = ()
    task_refs: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    automation: BddAutomation | None = None


__all__ = [
    "BDD_AUTOMATION_STATUSES",
    "BddAutomation",
    "BddExample",
    "DEFAULT_BDD_AUTOMATION_STATUS",
]
