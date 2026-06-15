---
schema_version: 4
id: quality-0100
type: quality_scenario
title: Agent can read model without build
status: accepted
section: quality_requirements
order: 70
quality: usability
source: read command execution
stimulus: Agent runs archledger read --json --body after source edits.
environment: normal_development
artifact: CLI JSON serialization
response: Current record bodies are returned without generating output files.
response_measure:
  "`archledger read --json --body` exits 0 and creates 0 build output
  files."
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

Agents can inspect model state without a build step.
