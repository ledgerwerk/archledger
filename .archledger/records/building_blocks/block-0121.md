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
  - Migration flows
protocol: YAML front matter + Markdown/AsciiDoc body
body_format: markdown
source_refs:
  - archledger/storage/frontmatter.py
  - archledger/repository.py
  - archledger/templates/records/
  - tests/test_frontmatter.py
kind: block
version: 1
---

This interface defines the record-file contract used by source fragments under `.archledger/records/`.

- **Provider**: storage/front matter parser/writer and repository record creation flows.
- **Consumers**: check/read/build pipelines, migration flows, and tooling that edits architecture records directly.
- **Protocol**: record files contain YAML front matter plus a body in the configured dialect (`body_format`) with required metadata fields validated by schema and checks.

The contract preserves deterministic parsing, explicit status/lifecycle metadata, and compatibility with source-schema v2 validation.
