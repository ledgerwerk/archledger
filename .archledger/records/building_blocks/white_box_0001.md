---
id: white_box_0001
type: white_box
title: Overall System
status: accepted
section: building_block_view
level: 1
parent: null
order: 10
diagram: null
quality_characteristics: []
tags: []
created_at: '2026-05-20T05:52:14Z'
updated_at: '2026-05-21T16:00:00Z'
source_refs:
- path: archledger/
  reason: All source code under the archledger package
---

## Motivation

archledger is decomposed into fifteen black boxes organized as a layered pipeline: the CLI accepts user input and delegates output formatting, the Config layer parses and renders project configuration, the Repository orchestrates business logic, the Model layer defines core data structures, the Record Type Registry maps record types to templates and defaults, the Check layer validates record content per type, the Source Ref Validation layer normalizes traceability links, the Storage layer handles file I/O, the Assembly layer renders the document, the Dialect layer abstracts format-specific markup, the Section Rendering layer handles per-record-type output, the Render layer orchestrates the build pipeline, the Converter layer handles multi-format export, the Source Tracking layer detects changes and impacts, and the Migration layer converts between source dialects.

## Contained building blocks

- **CLI Layer** (`cli.py`, `cli_formatting.py`, `cli_payloads.py`, `launcher.py`): Typer-based command-line interface with 11 top-level commands and a `source` subgroup (snapshot, changed, convert), JSON payload construction, and human-readable output formatting
- **Config Layer** (`config/`): Project configuration model, TOML parsing, default config rendering
- **Repository Layer** (`repository.py`): Business logic orchestration for init, create, list, check, status
- **Model Layer** (`model.py`, `errors.py`): Core data structures, validation constants, record lifecycle
- **Record Type Registry** (`record_types.py`): Record type specifications, directory/template/section mappings, CLI kind aliases
- **Check Layer** (`checks.py`): Per-record-type content validation and warning generation
- **Source Ref Validation** (`source_refs.py`): Traceability link normalization and path validation
- **Storage Layer** (`storage/`): File system access, front matter parsing, source state persistence
- **Assembly Layer** (`assembly.py`): Jinja2-based document assembly from records and sections
- **Dialect Layer** (`dialects.py`): Format-neutral markup abstraction (Markdown, AsciiDoc)
- **Section Rendering Layer** (`section_rendering.py`): Per-record-type rendering via dialects
- **Render Layer** (`render.py`): Build pipeline facade
- **Converter Layer** (`converters.py`, `conversion_plan.py`, `formats.py`): Multi-format export planning and execution via pandoc/asciidoctor
- **Source Tracking Layer** (`source_tracking.py`, `storage/source_state.py`): Change detection and impact analysis
- **Migration Layer** (`migration.py`): Source dialect conversion (Markdown to AsciiDoc)

## Important interfaces

The primary interface is the CLI (`archledger` console script). The CLI delegates to `cli_payloads.py` for JSON output construction and `cli_formatting.py` for human-readable messages. Internally, the Repository exposes methods that the CLI calls, and the Repository delegates to Storage, Model, Record Type Registry, Check, and Source Ref Validation. Config parsing is handled by the Config Layer independently from Storage. The Render Layer delegates to Assembly and Converters. The Converter Layer uses `conversion_plan.py` to plan each format conversion. Source Tracking is used by the CLI `source` subgroup for snapshot/changed/convert commands.
