---
id: block-0041
type: white_box
title: Overall System
schema_version: 4
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: null
order: 10
diagram: null
quality_characteristics: []
tags: []
source_refs:
  - path: archledger/
    reason: All source code under the archledger package
kind: block
version: 2
---

## Motivation

Archledger is decomposed into focused services within one source-first
architecture ledger. The package separates CLI presentation, repository and
model validation, storage, record mutation, rendering, conversion, source
tracking, and evidence queries. Behavior specifications and cross-ledger
workflow semantics are explicit external concerns.

## Principal building blocks

- **CLI and payload formatting**: Typer commands, human output, and stable JSON
  envelopes.
- **Config, Storage, Repository, and Model**: path resolution, front-matter I/O,
  orchestration, record loading, typed metadata validation, and references.
- **Record Type Registry and Record Mutation Service**: type-specific metadata
  contracts, templates, versioned writes, complete-document apply, and rollback.
- **Check, source-ref, test-ref, link, and scope services**: specialized source
  model validation and traceability.
- **Assembly, Dialect, Section Rendering, Render, Diagram, and Converter
  services**: native document construction and optional external conversion.
- **Source Tracking, Context, Trace, and combo trace**: drift detection, bounded
  record selection, and evidence traversal.
- **Migration, identity, ledger sequence, ID segment, and Renumber services**:
  safe evolution of source format and record identity.

## Important interfaces

The `archledger` CLI is the product interface. It delegates reads and checks to
the repository, writes to the Record Mutation Service, and rendering to the
assembly and converter path. Config parsing and storage remain independent of
presentation. Source Tracking feeds changed-file context queries. Context and
Trace return architecture evidence only; they do not coordinate behavior specs
or external ledgers.
