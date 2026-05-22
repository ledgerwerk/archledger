---
schema_version: 2
id: requirement_0007
type: requirement
title: "Source tracking reports changes impacts and unlinked files"
status: accepted
section: introduction_and_goals
order: 70
date: "2026-05-21"
source: "archledger CLI behavior and repository implementation"
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:42Z"
updated_at: "2026-05-21T18:18:42Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
---

## Requirement

`source snapshot` and `source changed` must report added/modified/deleted files, possible renames, impacted records, and unlinked files.

## Rationale

Documentation drift should be discoverable and actionable.
