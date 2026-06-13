---
id: block-0041
type: white_box
title: Overall System
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: null
order: 10
diagram: null
quality_characteristics: []
tags: []
created_at: "2026-05-20T05:52:14Z"
updated_at: "2026-05-22T07:00:00Z"
source_refs:
  - path: archledger/
    reason: All source code under the archledger package
kind: block
---

## Motivation

archledger is decomposed into focused black-box building blocks within one white-box system. The current Building Block View includes CLI, Config, Repository, Render, Storage, Model, Assembly, Dialect, Section Rendering, Converter, Source Tracking, Migration, Record Type Registry, Check, Source Ref Validation, ID Utilities, Renumber Service, ID Segment Resolution, and specification and traceability services.

## Contained building blocks

- **CLI Layer** (`cli.py`, `cli_formatting.py`, `cli_payloads.py`, `launcher.py`): Typer-based command-line interface with 14 top-level commands plus the `source` subgroup (`snapshot`, `changed`, `convert`), JSON payload construction, and human-readable output formatting
- **Config Layer** (`config/`): Project configuration model, TOML parsing, default config rendering
- **Repository Layer** (`repository.py`): Business logic orchestration for init, create, list/show/read, check, archive, doctor, and status workflows
- **Model Layer** (`model.py`, `errors.py`): Core data structures, validation constants, record lifecycle
- **Record Type Registry** (`record_types.py`): Record type specifications, directory/template/section mappings, CLI kind aliases
- **Check Layer** (`checks.py`): Per-record-type content validation including multi-type diagram validation (text/ascii/unicode/svgbob/mermaid) with dialect-specific block detection and line-length checks
- **Source Ref Validation** (`source_refs.py`): Traceability link normalization and path validation
- **Storage Layer** (`storage/`): File system access, front matter parsing, source state persistence
- **Assembly Layer** (`assembly.py`): Jinja2-based document assembly from records and sections
- **Dialect Layer** (`dialects.py`): Format-neutral markup abstraction (Markdown, AsciiDoc)
- **Section Rendering Layer** (`section_rendering.py`): Per-record-type rendering via dialects
- **Render Layer** (`render.py`): Build pipeline facade
- **Converter Layer** (`converters.py`, `conversion_plan.py`, `formats.py`): Multi-format export planning and execution via pandoc/asciidoctor
- **Source Tracking Layer** (`source_tracking.py`, `storage/source_state.py`): Change detection and impact analysis
- **Migration Layer** (`migration.py`): Source dialect conversion (Markdown to AsciiDoc)
- **ID Utilities** (`ids.py`): ID parsing and formatting helpers for ledger-prefixed IDs
- **Renumber Service** (`renumber.py`): ID migration planning and apply operations across records and links
- **ID Segment Resolution** (`id_segments.py`): Segment-aware ID routing and section scoping logic
- **Specification and Traceability Services** (`sdd.py`, `context.py`, `trace.py`, `mutations.py`, `bdd/`): SDD policy enforcement, bounded agent context, record trace traversal, validated record mutation, and Gherkin/pytest traceability interop

## Important interfaces

The primary interface is the CLI (`archledger` console script). The CLI delegates to `cli_payloads.py` for JSON output construction and `cli_formatting.py` for human-readable messages. Internally, the Repository exposes source-model operations used by the CLI and specification services, and delegates persistence to Storage. Config parsing is handled by the Config Layer independently from Storage. The Render Layer delegates to Assembly and Converters. Source Tracking feeds `source changed`, focused context queries, and the SDD pull-request gate. SDD, context, trace, mutation, and BDD modules remain domain services; the CLI owns command gating and presentation.
