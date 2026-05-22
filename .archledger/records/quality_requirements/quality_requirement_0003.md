---
schema_version: 2
id: quality_requirement_0003
type: quality_requirement
title: "Safe path validation"
status: accepted
section: quality_requirements
order: 30
date: "2026-05-21"
category: safety
source: "release architecture review"
measure: "Path escape attempts are rejected with explicit errors."
scenarios: ["quality_scenario_0006"]
body_format: markdown
created_at: "2026-05-21T18:18:45Z"
updated_at: "2026-05-21T18:18:45Z"
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
---

## Requirement

Path validation must reject relative parent traversal and out-of-root writes.

## Measurement

- Invalid configured/output paths fail validation with a clear message.
