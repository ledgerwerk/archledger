---
schema_version: 2
id: al_content_0014
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
updated_at: "2026-05-22T21:48:00Z"
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_init_cli.py
---

## Requirement

`archledger init` must create a complete, runnable project scaffold: config, storage metadata, section files, records directories, and skill defaults. The init command accepts CLI options for all configuration domains (build defaults, diagram settings, arc42 metadata, and source tracking) so that projects can be fully configured at creation time without manual TOML editing.

## Rationale

A fresh repository should become architecture-documentation-ready with a single command.
