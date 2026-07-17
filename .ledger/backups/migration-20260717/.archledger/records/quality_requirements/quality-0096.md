---
schema_version: 4
id: quality-0096
type: quality_requirement
title: JSON output stability
status: accepted
section: quality_requirements
order: 50
category: compatibility
source: release architecture review
measure: JSON payload keys for stable commands remain backward compatible.
scenarios:
  - quality-0100
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

## Requirement

Machine-readable CLI output must stay stable enough for automation consumers.

## Measurement

- `--json` responses for key commands keep stable schema across patch releases.
