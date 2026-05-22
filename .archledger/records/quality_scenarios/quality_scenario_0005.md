---
schema_version: 2
id: quality_scenario_0005
type: quality_scenario
title: "Source tracking detects rename"
status: accepted
section: quality_requirements
order: 50
date: "2026-05-21"
quality: "traceability"
source: "source changed analysis"
stimulus: "A tracked file is renamed with unchanged contents."
environment: "normal_development"
artifact: "source tracking pipeline"
response: "Possible rename is reported alongside impacts."
response_measure: "`source changed --json` includes at least one rename candidate with source/target paths and confidence >= 0.5."
body_format: markdown
created_at: "2026-05-21T18:18:54Z"
updated_at: "2026-05-21T18:18:54Z"
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
---

Source tracking detects rename candidates and keeps impact mapping.
