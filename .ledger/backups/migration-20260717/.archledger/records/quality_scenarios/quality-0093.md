---
schema_version: 4
id: quality-0093
type: quality_scenario
title: Native build does not require converters
status: accepted
section: quality_requirements
order: 30
quality: portability
source: build command + converter resolution
stimulus: User runs native markdown/asciidoc build on a clean Python environment.
environment: normal_development
artifact: native build pipeline
response: Build completes without invoking external converters.
response_measure: Exit code 0 and no converter invocation.
body_format: markdown
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

Native source-format builds run without pandoc/asciidoctor dependencies.
