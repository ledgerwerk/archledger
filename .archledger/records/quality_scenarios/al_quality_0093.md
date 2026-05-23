---
schema_version: 2
id: al_quality_0093
type: quality_scenario
title: Native build does not require converters
status: accepted
section: quality_requirements
order: 30
date: "2026-05-21"
quality: portability
source: build command + converter resolution
stimulus: User runs native markdown/asciidoc build on a clean Python environment.
environment: normal_development
artifact: native build pipeline
response: Build completes without invoking external converters.
response_measure: Exit code 0 and no converter invocation.
body_format: markdown
created_at: "2026-05-21T18:18:53Z"
updated_at: "2026-05-21T18:18:53Z"
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
---

Native source-format builds run without pandoc/asciidoctor dependencies.
