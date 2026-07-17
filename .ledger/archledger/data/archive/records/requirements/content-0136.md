---
schema_version: 4
id: content-0136
type: requirement
title: SDD profile enforces specification traceability contracts
status: archived
section: introduction_and_goals
order: 110
source: SDD profile implementation and CLI tests
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
source_refs:
  - path: archledger/sdd.py
    role: implements
    reason: Evaluates requirement, ADR, quality-scenario, reference, and BDD policy.
  - path: archledger/cli.py
    role: implements
    reason: Exposes status, check, and pull-request gate commands.
test_refs:
  - tests/test_sdd_cli.py
  - tests/test_sdd_pr_cli.py
acceptance_criteria:
  - id: AC-001
    statement:
      Strict SDD check reports accepted requirements that lack criteria, implementation
      references, or validation and exits non-zero.
    validation:
      command: pytest -q tests/test_sdd_cli.py tests/test_sdd_pr_cli.py
      expected: passes
kind: content
version: 2
archived_reason: Removed SDD orchestration belongs to an external organizer, not Archledger.
archived_from: records/requirements/content-0136.md
---

## Requirement

When the SDD profile is enabled, Archledger must evaluate source records against
the configured specification and traceability policy. The policy covers
acceptance criteria, implementation references, test references, ADR links,
quality-scenario completeness, reference validity, and optional BDD metadata.

## Rationale

Architecture records become enforceable development contracts rather than
unstructured prose, while projects retain explicit profile-level control over
which checks are mandatory.
