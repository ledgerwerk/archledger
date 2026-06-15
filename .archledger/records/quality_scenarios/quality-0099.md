---
schema_version: 4
id: quality-0099
type: quality_scenario
title: Output path cannot escape build directory
status: accepted
section: quality_requirements
order: 60
quality: safety
source: output path resolution
stimulus: Config or CLI sets an escaping output path such as ../architecture.md.
environment: normal_development
artifact: path validation
response: Command rejects the path before writing.
response_measure:
  Invalid escaping output path causes non-zero exit and an error mentioning
  root-bound path validation.
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

Output path validation prevents directory escape.
