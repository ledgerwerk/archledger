---
schema_version: 4
id: block-0121
type: interface
title: Front matter record file contract
status: accepted
section: building_block_view
parent: null
order: 20
providers:
  - Storage layer
  - Repository layer
consumers:
  - Check/read/build pipelines
  - Record Mutation Service
  - Migration flows
protocol: YAML front matter + Markdown/AsciiDoc body
body_format: markdown
source_refs:
  - archledger/storage/frontmatter.py
  - archledger/repository.py
  - archledger/model.py
  - archledger/record_types.py
  - archledger/mutations.py
  - archledger/templates/records/
  - tests/test_frontmatter.py
  - tests/test_mutation_cli.py
kind: block
version: 2
---

This interface defines canonical record files under `.archledger/records/` and
section files under the active profile. Each document contains YAML front matter
plus a Markdown or AsciiDoc body.

The contract includes stable record identity, kind and type, lifecycle status,
section and order, body format, and a monotonically increasing version. The
Record Type Registry adds per-type metadata shapes. Repository checks validate
identity, filenames, typed metadata, source and test references, and
cross-record links.

Storage parses and writes the document. The Record Mutation Service preserves ID
and kind, ignores externally supplied version changes, increments once for a
logical change, and supports rollback after failed validation.
