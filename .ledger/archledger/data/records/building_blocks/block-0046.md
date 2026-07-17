---
id: block-0046
type: black_box
title: Model Layer
schema_version: 4
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
  - validate_record_metadata_shape()
  - filename_for()
  - record_sort_key()
  - normalize_kind()
location:
  - archledger/model.py
  - archledger/errors.py
fulfilled_requirements: []
risks: []
tags: []
source_refs:
  - archledger/model.py
  - archledger/errors.py
kind: block
version: 2
---

The Model Layer defines immutable architecture records, normalized source
references, validation constants, and core record invariants. `validate_record()`
checks field types, lifecycle status, identifier and filename consistency, and
segment expectations.

Metadata-shape validation obtains field specifications from the Record Type
Registry and verifies strings, integers, booleans, string lists, objects, and
object lists. Diagnostics identify the record and field, report the observed
shape, and provide a typed `record meta set` repair example. Archive tombstones
and section records use their dedicated contracts.

Specialized source-reference validation remains in `source_refs.py`; record type
definitions remain in `record_types.py`; domain exceptions remain in
`errors.py`.
