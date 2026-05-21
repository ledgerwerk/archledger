---
id: white_box_0001
type: white_box
title: "Overall System"
status: accepted
section: building_block_view
level: 1
parent: null
order: 10
diagram: null
quality_characteristics: []
tags: []
created_at: "2026-05-20T05:52:14Z"
updated_at: "2026-05-20T12:00:00Z"
---

## Motivation

archledger is decomposed into eleven black boxes organized as a layered pipeline: the CLI accepts user input, the Repository orchestrates business logic, the Model defines data structures and validation rules, the Storage layer handles file I/O, the Assembly layer renders the document, the Dialect layer abstracts format-specific markup, the Section Rendering layer handles per-record-type output, the Render layer is a thin facade orchestrating the build, the Converter layer handles multi-format export, the Source Tracking layer detects changes and impacts, and the Migration layer converts between source dialects.

## Contained building blocks

- **CLI Layer** (`cli.py`, `launcher.py`): Typer-based command-line interface with 13 commands
- **Repository Layer** (`repository.py`): Business logic orchestration for init, create, list, check, status
- **Render Layer** (`render.py`): Thin build pipeline facade
- **Storage Layer** (`storage/`): File system access, front matter parsing, config loading, source state persistence
- **Model Layer** (`model.py`, `errors.py`): Data structures, validation, type mappings, SourceRef
- **Assembly Layer** (`assembly.py`): Jinja2-based document assembly from records and sections
- **Dialect Layer** (`dialects.py`): Format-neutral markup abstraction (Markdown, AsciiDoc)
- **Section Rendering Layer** (`section_rendering.py`): Per-record-type rendering via dialects
- **Converter Layer** (`converters.py`, `formats.py`): Multi-format export via pandoc/asciidoctor
- **Source Tracking Layer** (`source_tracking.py`, `storage/source_state.py`): Change detection and impact analysis
- **Migration Layer** (`migration.py`): Source dialect conversion (Markdown to AsciiDoc)

## Important interfaces

The primary interface is the CLI (`archledger` console script). Internally, the Repository exposes methods that the CLI calls, and the Repository delegates to Storage and Model. The Assembly Layer delegates to Section Rendering and Dialects. The Render Layer delegates to Assembly and Converters. Source Tracking is used directly by the CLI for snapshot/changed commands.
