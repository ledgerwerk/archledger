---
schema_version: 2
id: requirement_0005
type: requirement
title: "Native build requires no external converter tools"
status: accepted
section: introduction_and_goals
order: 50
date: "2026-05-21"
source: "archledger CLI behavior and repository implementation"
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:41Z"
updated_at: "2026-05-21T18:18:41Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
---

## Requirement

Native builds (Markdown->Markdown, AsciiDoc->AsciiDoc) must run without pandoc/asciidoctor installations.

## Rationale

Core workflows should work in minimal Python-only environments.
