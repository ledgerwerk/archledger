---
schema_version: 2
id: al_adr_0081
type: adr
title: Config v5 and source schema v2 are the release baseline
status: accepted
section: architecture_decisions
order: 50
date: "2026-05-21"
deciders:
  - archledger maintainers
supersedes: []
related: []
tags: []
body_format: markdown
created_at: "2026-05-21T18:18:50Z"
updated_at: "2026-05-21T18:18:50Z"
source_refs:
  - archledger/repository.py
  - archledger/cli.py
  - tests/test_repository_cli.py
---

## Context

Repository-local architecture sources must use one supported baseline schema to avoid drift between project dogfooding and generated defaults.

## Decision

Use config v5 and source schema v2 as the release baseline for this project and generated projects.

## Consequences

Strict checks are consistent; migration effort is required for older local records.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.
