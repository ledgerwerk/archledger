---
schema_version: 2
id: content-0014
type: requirement
title: Project initialization creates archledger workspace structure
status: accepted
section: introduction_and_goals
order: 10
date: "2026-05-22"
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-05-21T18:18:39Z"
updated_at: "2026-06-07T09:10:37Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_init_cli.py
  - path: archledger/cli.py
    role: implements
    reason: Implements project initialization command and options.
acceptance_criteria:
  - id: AC-001
    statement:
      Running init in an empty directory creates config, storage metadata,
      arc42 section sources, record directories, and configured profile defaults.
    validation:
      command: pytest -q tests/test_init_cli.py
      expected: passes
test_refs:
  - tests/test_init_cli.py
kind: content
---

## Requirement

`archledger init` must create a complete, runnable project scaffold: config, storage metadata, section files, records directories, and skill defaults. The init command accepts CLI options for all configuration domains (build defaults, diagram settings, arc42 metadata, and source tracking) so that projects can be fully configured at creation time without manual TOML editing.

## Rationale

A fresh repository should become architecture-documentation-ready with a single command.
