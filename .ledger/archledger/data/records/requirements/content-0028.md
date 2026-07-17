---
schema_version: 4
id: content-0028
type: requirement
title: Local-first operation requires no network services
status: accepted
section: introduction_and_goals
order: 100
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
    reason: Provides local filesystem-backed repository operations.
acceptance_criteria:
  - id: AC-001
    statement:
      Read, check, and native build complete using only local files and processes,
      with no required server, database, or network call.
    validation:
      command: pytest -q tests/test_read_cli.py tests/test_build.py
      expected: passes
test_refs:
  - tests/test_read_cli.py
  - tests/test_build.py
kind: content
version: 1
---

## Requirement

Normal operation must be local-first: no server process, database, or network access required for read/check/build workflows.

## Rationale

Preserves privacy and offline reliability.
