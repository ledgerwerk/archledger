---
schema_version: 2
id: al_adr_0084
type: adr
title: Output path resolution remains bounded to configured roots
status: accepted
section: architecture_decisions
order: 80
date: "2026-05-21"
deciders:
  - archledger maintainers
supersedes: []
related: []
tags: []
body_format: markdown
created_at: "2026-05-21T18:18:51Z"
updated_at: "2026-05-21T18:18:51Z"
source_refs:
  - archledger/repository.py
  - archledger/cli.py
  - tests/test_repository_cli.py
---

## Context

Architecture output generation must not permit accidental writes outside intended roots.

## Decision

Keep output path resolution bounded by configuration/workspace validation rules.

## Consequences

Safer defaults; invalid paths fail early with explicit diagnostics.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.
