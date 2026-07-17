---
schema_version: 4
id: content-0022
type: requirement
title: Read current architecture model without export
status: accepted
section: introduction_and_goals
order: 40
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
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
kind: content
version: 1
---

## Requirement

`archledger read --json --body` must expose the current model without generating output artifacts.

## Rationale

Agents and CI should inspect architecture state directly from sources.
