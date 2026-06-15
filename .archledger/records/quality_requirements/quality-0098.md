---
schema_version: 4
id: quality-0098
type: quality_requirement
title: Source tracking correctness
status: accepted
section: quality_requirements
order: 60
category: correctness
source: release architecture review
measure: Source tracking reports file and impact deltas accurately.
scenarios:
  - quality-0097
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

## Requirement

Source tracking must correctly classify file changes and impact mappings.

## Measurement

- Rename, modify, and unlinked-file scenarios are covered by tests and command output.
