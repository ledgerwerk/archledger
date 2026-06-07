---
schema_version: 2
id: al_content_0137
type: requirement
title: "Agent context and trace queries return focused architecture evidence"
status: proposed
section: introduction_and_goals
order: 120
date: "2026-06-07"
source: Agent context and trace implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-06-07T09:11:14Z"
updated_at: "2026-06-07T09:11:14Z"
source_refs:
  - path: archledger/context.py
    role: implements
    reason: Selects bounded records for file, record, and changed-file queries.
  - path: archledger/trace.py
    role: implements
    reason: Builds relationship and evidence views rooted at a record.
test_refs:
  - tests/test_context_cli.py
  - tests/test_sdd_cli.py
acceptance_criteria:
  - id: AC-001
    statement: Context and trace commands return JSON evidence focused on the requested file, record, or current source changes without requiring a build.
    validation:
      command: pytest -q tests/test_context_cli.py tests/test_sdd_cli.py
      expected: passes
---

## Requirement

`archledger context` must return a compact set of relevant records for a source
file, record ID, or changed-file set. `archledger trace` must expose the
requirements, decisions, acceptance criteria, source references, and test
references connected to a selected record.

## Rationale

Coding agents need bounded, machine-readable architecture evidence to make
source changes without loading or rebuilding the complete document.
