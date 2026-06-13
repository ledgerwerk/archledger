---
schema_version: 2
id: content-0023
type: requirement
title: Native build requires no external converter tools
status: accepted
section: introduction_and_goals
order: 50
date: "2026-05-21"
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:41Z"
updated_at: "2026-06-07T09:10:47Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
  - path: archledger/render.py
    role: implements
    reason: Renders native source formats without converter invocation.
acceptance_criteria:
  - id: AC-001
    statement:
      A native Markdown or AsciiDoc build succeeds when external converter
      executables are unavailable.
    validation:
      command: pytest -q tests/test_build.py
      expected: passes
test_refs:
  - tests/test_build.py
kind: content
---

## Requirement

Native builds (Markdown->Markdown, AsciiDoc->AsciiDoc) must run without pandoc/asciidoctor installations.

## Rationale

Core workflows should work in minimal Python-only environments.
