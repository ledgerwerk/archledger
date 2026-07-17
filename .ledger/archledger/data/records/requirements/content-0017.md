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
  - path: archledger/mutations.py
    role: implements
    reason: Provides identity-preserving versioned record updates.
acceptance_criteria:
  - id: AC-001
    statement:
      Markdown and AsciiDoc records round-trip as YAML-front-matter source
      files in the configured records directory.
    validation:
      command: pytest -q tests/test_frontmatter.py tests/test_read_cli.py
      expected: passes
  - id: AC-002
    statement:
      Supported CLI mutations preserve identity, apply typed metadata, increment
      version once for changes, and restore the target after validation failure.
    validation:
      command: pytest -q tests/test_mutation_cli.py
      expected: passes
test_refs:
  - tests/test_frontmatter.py
  - tests/test_read_cli.py
  - tests/test_mutation_cli.py
kind: content
version: 2
---

## Requirement

Architecture source must remain human-editable Markdown or AsciiDoc with YAML
front matter stored in the repository. Existing records must support typed,
version-aware CLI mutation and complete-document export/apply without allowing
identity or kind replacement. A failed post-write validation must restore the
original record.

## Rationale

The architecture model remains reviewable and diffable while coding agents gain
a safe write path that preserves source-model invariants.
