---
schema_version: 4
id: quality-0101
type: quality_scenario
title: Config v7 and source schema v2 records validate strictly
status: accepted
section: quality_requirements
order: 80
quality: maintainability
source: strict check
stimulus:
  Repository records include schema_version/date/body_format in source schema
  v2.
environment: normal_development
artifact: validation pipeline
response: Strict check passes without schema/date/body_format findings.
response_measure: archledger check --strict exits 0.
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

Config v7 plus source schema v2 records validate in strict mode.
