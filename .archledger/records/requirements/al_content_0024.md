---
schema_version: 2
id: al_content_0024
type: requirement
title: Multi-format export supports configured converter tools
status: accepted
section: introduction_and_goals
order: 60
date: "2026-05-21"
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:41Z"
updated_at: "2026-06-07T09:10:49Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
  - path: archledger/converters.py
    role: implements
    reason: Selects and invokes configured export converters.
acceptance_criteria:
  - id: AC-001
    statement:
      Each supported non-native format either produces the requested artifact
      through the configured converter or fails with actionable missing-tool guidance.
    validation:
      command: pytest -q tests/test_build.py
      expected: passes
test_refs:
  - tests/test_build.py
---

## Requirement

Non-native exports (HTML, PDF, DOCX, RST, Textile) must be supported through configured external converters with explicit install guidance on failure.

## Rationale

Users need multi-format output while keeping conversion logic delegated.
