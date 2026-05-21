---
schema_version: 2
id: black_box_0014
type: black_box
title: Check Layer
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 125
date: '2026-05-21'
interfaces:
- content_warnings()
location:
- archledger/checks.py
fulfilled_requirements: []
risks: []
tags: []
body_format: markdown
created_at: '2026-05-21T11:32:00Z'
updated_at: '2026-05-21T11:32:00Z'
source_refs:
- archledger/checks.py
---

The `checks.py` module provides per-record-type content validation beyond structural checks. The main entry point is `content_warnings()`, which returns a list of warning strings for a given `ArchitectureRecord`. It dispatches to type-specific checkers registered in `_CONTENT_WARNING_CHECKERS`: quality goals require scenarios, stakeholders require expectations, constraints require impact and valid categories, ADRs require Context/Decision/Consequences sections and deciders, quality scenarios require measurable response measures, risks require valid severity/probability and mitigation, and so on. It also detects placeholder text in record bodies and cross-dialect syntax contamination (e.g., AsciiDoc headings in Markdown records). This module was extracted from `repository.py` to isolate validation logic.
