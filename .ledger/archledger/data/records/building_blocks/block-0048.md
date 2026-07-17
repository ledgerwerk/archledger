---
id: block-0048
type: black_box
title: Dialect Layer
schema_version: 4
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: block-0041
order: 70
interfaces:
  - get_dialect()
  - Dialect base class
  - MarkdownDialect / AsciiDocDialect
location:
  - archledger/dialects.py
fulfilled_requirements: []
risks: []
tags: []
source_refs:
  - archledger/dialects.py
kind: block
version: 1
---

The dialects module provides a format-neutral abstraction for document rendering. The `Dialect` base class defines methods for headings, tables, bullets, and strong text. `MarkdownDialect` and `AsciiDocDialect` implement these using the respective markup conventions (e.g., `#` vs `=` for headings, `|...|` vs `|===` tables). Both the Assembly Layer and Section Rendering Layer use dialects to produce format-correct output without conditional branching.
