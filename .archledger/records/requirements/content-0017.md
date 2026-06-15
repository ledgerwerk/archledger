---
schema_version: 4
id: content-0017
type: requirement
title: File-based source model uses editable records
status: accepted
section: introduction_and_goals
order: 20
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
  - path: archledger/storage/frontmatter.py
    role: implements
    reason: Parses and writes canonical source records.
acceptance_criteria:
  - id: AC-001
    statement:
      Markdown and AsciiDoc records round-trip as YAML-front-matter source
      files in the configured records directory.
    validation:
      command: pytest -q tests/test_frontmatter.py tests/test_read_cli.py
      expected: passes
test_refs:
  - tests/test_frontmatter.py
  - tests/test_read_cli.py
kind: content
version: 1
---

## Requirement

Architecture source must be human-editable files (Markdown/AsciiDoc) with YAML front matter stored in the repository.

## Rationale

The architecture model is reviewable, diffable, and versioned together with code.
