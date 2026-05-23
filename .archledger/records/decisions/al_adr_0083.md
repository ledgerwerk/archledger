---
schema_version: 2
id: al_adr_0083
type: adr
title: Non-native exports delegate to pandoc or asciidoctor
status: accepted
section: architecture_decisions
order: 70
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

Supporting many export formats inside Python would duplicate mature tooling and increase maintenance burden.

## Decision

Delegate non-native conversions to pandoc/asciidoctor family tools.

## Consequences

Clear dependency errors are required when tools are missing.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.
