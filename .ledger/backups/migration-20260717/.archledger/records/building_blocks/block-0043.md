---
id: block-0043
type: black_box
title: Repository Layer
schema_version: 4
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: block-0041
order: 20
interfaces:
  - create_record()
  - list_records()
  - get_record()
  - load_all_records()
  - check()
  - init()
  - status()
location:
  - archledger/repository.py
fulfilled_requirements: []
risks: []
tags: []
source_refs:
  - archledger/repository.py
kind: block
version: 1
---

The `ArchitectureRepository` class is the central business logic layer. It orchestrates record creation (allocating IDs via the Record Type Registry using the configured `LedgerIdFormat` and segment resolution from `id_segments.py`, rendering templates, writing files), record loading (parsing front matter, validating fields including ID syntax and segment expectations, normalizing source refs via the Source Ref Validation layer), integrity checks (delegating per-record-type content warnings to the Check Layer, plus cross-reference validation and source contract validation), and initialization (directory scaffolding, section file generation with init-time ID format options). It holds a Jinja2 environment for template rendering.

Record ID allocation uses `ProjectConfig.id_format` to format the next number with the configured prefix, width, and segment. In segmented mode, the segment is resolved via `id_segment_for_new_record()` from the record kind and config `segment_map`.
