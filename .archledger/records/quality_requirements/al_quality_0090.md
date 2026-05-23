---
schema_version: 2
id: al_quality_0090
type: quality_requirement
title: Fast check and build on small repositories
status: accepted
section: quality_requirements
order: 20
date: "2026-05-21"
category: performance
source: release architecture review
measure: check/build complete in under 5s on representative small repositories.
scenarios:
  - al_quality_0101
body_format: markdown
created_at: "2026-05-21T18:18:44Z"
updated_at: "2026-05-21T18:18:44Z"
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
---

## Requirement

`archledger check` and native `archledger build` should be fast on small repositories.

## Measurement

- Typical developer project check/build completes within a few seconds on commodity hardware.
