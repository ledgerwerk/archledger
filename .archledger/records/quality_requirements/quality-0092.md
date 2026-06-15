---
schema_version: 4
id: quality-0092
type: quality_requirement
title: Safe path validation
status: accepted
section: quality_requirements
order: 30
category: safety
source: release architecture review
measure: Path escape attempts are rejected with explicit errors.
scenarios:
  - quality-0099
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

## Requirement

Path validation must reject relative parent traversal and out-of-root writes.

## Measurement

- Invalid configured/output paths fail validation with a clear message.
