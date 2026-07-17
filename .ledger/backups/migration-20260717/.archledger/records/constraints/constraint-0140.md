---
schema_version: 4
id: constraint-0140
kind: constraint
type: constraint
title: Archledger remains an isolated architecture ledger
status: accepted
section: architecture_constraints
order: 60
version: 3
category: technical
impact:
  Archledger stores only architecture records, links, and source evidence; behavior
  specifications and cross-ledger workflow policy remain external.
body_format: markdown
source_refs:
  - path: README.md
    role: documents
    reason: Defines the architecture-ledger boundary.
  - path: skills/archledger/SKILL.md
    role: documents
    reason:
      Guides agents to keep behavior specifications and organizer semantics outside
      Archledger.
  - path: tests/test_skill_file.py
    role: validates
    reason: Verifies agent guidance preserves the isolated-ledger boundary.
test_refs:
  - tests/test_skill_file.py
---

Archledger is the source-first ledger for architecture records, arc42 sections,
record links, and source or test evidence. It does not own behavior-specification
artifacts, execute BDD workflows, enforce software-development lifecycle policy,
or interpret relationships between independent ledgers.

External artifacts may be referenced through opaque links or source references.
Semantic coordination belongs to an external organizer. Behavior specifications
in this repository are maintained by SpecMason and remain outside the
Archledger record model.

This boundary keeps architecture validation deterministic and prevents
Archledger from becoming a general workflow orchestrator.
