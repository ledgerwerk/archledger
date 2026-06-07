---
schema_version: 2
id: al_content_0022
type: requirement
title: Read current architecture model without export
status: accepted
section: introduction_and_goals
order: 40
date: "2026-05-21"
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:41Z"
updated_at: "2026-06-07T09:10:44Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
  - path: archledger/repository.py
    role: implements
    reason: Loads the canonical architecture model directly from source records.
acceptance_criteria:
  - id: AC-001
    statement:
      JSON read with bodies returns current source records and does not create
      or modify build output.
    validation:
      command: pytest -q tests/test_read_cli.py
      expected: passes
test_refs:
  - tests/test_read_cli.py
---

## Requirement

`archledger read --json --body` must expose the current model without generating output artifacts.

## Rationale

Agents and CI should inspect architecture state directly from sources.
