---
schema_version: 2
id: quality_requirement_0001
type: quality_requirement
title: "Deterministic native build output"
status: accepted
section: quality_requirements
order: 10
date: "2026-05-21"
category: reliability
source: "release architecture review"
measure: "Byte-identical output for equal accepted records and deterministic date source."
scenarios: ["quality_scenario_0003", "quality_scenario_0008"]
body_format: markdown
created_at: "2026-05-21T18:18:44Z"
updated_at: "2026-05-21T18:18:44Z"
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
---

## Requirement

Build output must be reproducible for unchanged accepted records.

## Measurement

- Repeated builds produce byte-identical output when SOURCE_DATE_EPOCH and records are unchanged.
