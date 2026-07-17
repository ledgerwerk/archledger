---
schema_version: 4
id: block-0054
type: black_box
title: Record Type Registry
status: accepted
section: building_block_view
level: 1
parent: block-0041
order: 115
interfaces:
  - RECORD_TYPES registry
  - CLI_KIND_ALIASES
  - RecordTypeSpec dataclass
  - MetadataFieldSpec dataclass
  - metadata_field_specs_for_record_type()
location:
  - archledger/record_types.py
fulfilled_requirements: []
risks: []
tags: []
body_format: markdown
source_refs:
  - archledger/record_types.py
  - path: archledger/templates/records/diagram.md.j2
    reason: Diagram template scaffolding per diagram type
  - path: archledger/templates/records/diagram.adoc.j2
    reason: Diagram template scaffolding per diagram type
kind: block
version: 2
---

`record_types.py` is the authoritative registry for arc42 record kinds. Each
`RecordTypeSpec` maps a kind to its directory, filename prefix, section,
template, aliases, default status and level, context factory, and typed metadata
fields.

`MetadataFieldSpec` describes supported value shapes and nullability. Shared
fields such as `applies_to`, `level`, and `parent` combine with per-type fields
for requirements, stakeholders, runtime scenarios, diagrams, interfaces, and
other records. The Model Layer consumes this contract during validation, while
CLI metadata mutation accepts explicit JSON, raw strings, or YAML/JSON files.

Diagram records default to text and support text, ascii, unicode, svgbob, and
mermaid content with type-specific scaffolding and checks.
