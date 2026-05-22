---
schema_version: 2
id: requirement_0010
type: requirement
title: "Local-first operation requires no network services"
status: accepted
section: introduction_and_goals
order: 100
date: "2026-05-21"
source: "archledger CLI behavior and repository implementation"
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:43Z"
updated_at: "2026-05-21T18:18:43Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
---

## Requirement

Normal operation must be local-first: no server process, database, or network access required for read/check/build workflows.

## Rationale

Preserves privacy and offline reliability.
