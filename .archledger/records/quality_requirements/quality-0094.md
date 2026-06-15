---
schema_version: 4
id: quality-0094
type: quality_requirement
title: Clear converter failure diagnostics
status: accepted
section: quality_requirements
order: 40
category: operability
source: release architecture review
measure: Converter failures identify missing tool and installation hint.
scenarios:
  - quality-0095
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

## Requirement

Missing converter dependencies must fail fast with actionable diagnostics.

## Measurement

- Failure output names the missing executable and gives install guidance.
