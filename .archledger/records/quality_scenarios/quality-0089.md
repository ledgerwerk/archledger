---
id: quality-0089
type: quality_scenario
title: Build produces identical output for identical inputs
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: quality_requirements
order: 10
quality: reliability
source: Developer
stimulus: Runs archledger build twice on the same set of accepted records
environment: normal_development
artifact: archledger build command
response: Both builds produce byte-identical output
response_measure: Zero lines of diff between the two output files
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
---

The build process must be deterministic: same records always produce the same document. No timestamps, random values, or external state should influence the output. This ensures reproducible documentation in CI pipelines.
