---
schema_version: 4
id: quality-0088
type: quality_requirement
title: Deterministic native build output
status: accepted
section: quality_requirements
order: 10
category: reliability
source: release architecture review
measure: Byte-identical output for equal accepted records and deterministic date source.
scenarios:
  - quality-0093
  - quality-0101
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

## Requirement

Build output must be reproducible for unchanged accepted records.

## Measurement

- Repeated builds produce byte-identical output when SOURCE_DATE_EPOCH and records are unchanged.
