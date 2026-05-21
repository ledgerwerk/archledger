---
id: black_box_0005
type: black_box
title: "Model Layer"
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 50
interfaces:
  - ArchitectureRecord dataclass
  - SourceRef dataclass
  - validate_record()
  - filename_for()
  - record_sort_key()
  - normalize_kind()
location:
  - archledger/model.py
  - archledger/errors.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T05:52:16Z"
updated_at: "2026-05-20T12:00:00Z"
---

The model module defines the core data structures and validation rules. `ArchitectureRecord` is a frozen dataclass holding id, type, title, status, section, order, path, metadata, body, and source_refs. `SourceRef` holds path, symbols, and reason for traceability linking. Constants define the mapping from record types to directory names, filename prefixes, default sections, and templates for both Markdown and AsciiDoc. `validate_record()` checks field types, status values, and ID/filename consistency. The `errors.py` module defines the exception hierarchy: `ArchledgerError` base with `ConfigError`, `StorageError`, `FrontMatterError`, `ValidationError`, and `RenderError` subclasses.
