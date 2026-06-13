---
schema_version: 2
id: content-0026
type: requirement
title: Path safety prevents writes outside allowed roots
status: accepted
section: introduction_and_goals
order: 80
date: "2026-05-21"
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:42Z"
updated_at: "2026-06-07T09:10:54Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
  - path: archledger/storage/paths.py
    role: implements
    reason: Resolves and validates workspace-bound paths.
acceptance_criteria:
  - id: AC-001
    statement:
      Storage, tracking, and build paths that escape their permitted root are
      rejected before any write occurs.
    validation:
      command: pytest -q tests/test_paths.py
      expected: passes
test_refs:
  - tests/test_paths.py
kind: content
---

## Requirement

Configured storage, tracking, and build output paths must be validated so they cannot escape their permitted workspace roots.

## Rationale

Prevents accidental or unsafe writes outside the project.
