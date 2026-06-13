---
id: block-0046
type: black_box
title: Model Layer
schema_version: 2
date: "2026-05-20"
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: block-0041
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
source_refs:
  - archledger/model.py
  - archledger/errors.py
kind: block
---

The model module defines the core data structures and validation rules. `ArchitectureRecord` is a frozen dataclass holding id, type, title, status, section, order, path, metadata, body, and source_refs. `SourceRef` holds path, symbols, and reason for traceability linking. `validate_record()` checks field types, status values, and ID/filename consistency. Constants for valid formats, status values, and file extension mappings remain in `model.py`. Record type to directory/template/section mappings have been extracted to the Record Type Registry (`record_types.py`). Source ref validation and normalization have been extracted to the Source Ref Validation layer (`source_refs.py`). The `errors.py` module defines the exception hierarchy: `ArchledgerError` base with `ConfigError`, `StorageError`, `FrontMatterError`, `ValidationError`, and `RenderError` subclasses.
