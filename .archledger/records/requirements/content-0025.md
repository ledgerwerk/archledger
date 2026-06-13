---
schema_version: 2
id: content-0025
type: requirement
title: Source tracking reports changes impacts and unlinked files
status: accepted
section: introduction_and_goals
order: 70
date: "2026-05-21"
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:42Z"
updated_at: "2026-06-07T09:10:51Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
  - path: archledger/source_tracking.py
    role: implements
    reason: Scans source state and computes drift.
acceptance_criteria:
  - id: AC-001
    statement:
      After a source snapshot, changed reports additions, modifications, deletions,
      possible renames, impacted records, and unlinked changed files in JSON.
    validation:
      command: pytest -q tests/test_source_tracking.py
      expected: passes
test_refs:
  - tests/test_source_tracking.py
kind: content
---

## Requirement

`source snapshot` and `source changed` must report added/modified/deleted files, possible renames, impacted records, and unlinked files.

## Rationale

Documentation drift should be discoverable and actionable.
