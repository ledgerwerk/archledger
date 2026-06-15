---
schema_version: 4
id: quality-0090
type: quality_requirement
title: Fast check and build on small repositories
status: accepted
section: quality_requirements
order: 20
category: performance
source: release architecture review
measure: check/build complete in under 5s on representative small repositories.
scenarios:
  - quality-0101
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

## Requirement

`archledger check` and native `archledger build` should be fast on small repositories.

## Measurement

- Typical developer project check/build completes within a few seconds on commodity hardware.
