---
id: black_box_0007
type: black_box
title: "Dialect Layer"
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
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
created_at: "2026-05-20T12:00:00Z"
updated_at: "2026-05-20T12:00:00Z"
---

The dialects module provides a format-neutral abstraction for document rendering. The `Dialect` base class defines methods for headings, tables, bullets, and strong text. `MarkdownDialect` and `AsciiDocDialect` implement these using the respective markup conventions (e.g., `#` vs `=` for headings, `|...|` vs `|===` tables). Both the Assembly Layer and Section Rendering Layer use dialects to produce format-correct output without conditional branching.
