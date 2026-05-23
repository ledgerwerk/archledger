---
schema_version: 2
id: al_adr_0080
type: adr
title: Use SHA-256-only source-state file entries plus directory hashes
status: accepted
section: architecture_decisions
order: 40
date: "2026-05-21"
deciders:
  - archledger maintainers
supersedes: []
related: []
tags: []
body_format: markdown
created_at: "2026-05-21T18:18:49Z"
updated_at: "2026-05-21T18:18:49Z"
source_refs:
  - archledger/repository.py
  - archledger/cli.py
  - tests/test_repository_cli.py
---

## Context

Source-state tracking needs strong change detection and compact persisted metadata.

## Decision

Persist per-file SHA-256 hashes only, plus derived directory hashes and counts in source state snapshots.

## Consequences

Improves determinism and avoids unstable file-size/mtime dependence; requires content hashing during scan.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.
