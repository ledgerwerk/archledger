---
schema_version: 2
id: al_content_0020
type: requirement
title: Record creation enforces schema and unique ids
status: accepted
section: introduction_and_goals
order: 30
date: "2026-05-21"
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:40Z"
updated_at: "2026-05-23T11:30:00Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - archledger/ids.py
  - archledger/id_segments.py
  - tests/test_read_cli.py
---

## Requirement

`archledger new` must allocate stable IDs using the configured `LedgerIdFormat` (prefix, width, and segment mode), resolve the segment token when in segmented mode, choose the correct filename/template, and write schema-compliant front matter for each supported record type.

## Rationale

Record creation needs to be safe for both humans and coding agents. IDs must be unique, globally sequential, and formatted according to project configuration.
