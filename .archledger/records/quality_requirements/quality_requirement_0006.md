---
schema_version: 2
id: quality_requirement_0006
type: quality_requirement
title: "Source tracking correctness"
status: accepted
section: quality_requirements
order: 60
date: "2026-05-21"
category: correctness
source: "release architecture review"
measure: "Source tracking reports file and impact deltas accurately."
scenarios: ["quality_scenario_0005"]
body_format: markdown
created_at: "2026-05-21T18:18:46Z"
updated_at: "2026-05-21T18:18:46Z"
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
---

## Requirement

Source tracking must correctly classify file changes and impact mappings.

## Measurement

- Rename, modify, and unlinked-file scenarios are covered by tests and command output.
