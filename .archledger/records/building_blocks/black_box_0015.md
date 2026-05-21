---
schema_version: 2
id: black_box_0015
type: black_box
title: Source Ref Validation
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 135
date: '2026-05-21'
interfaces:
- normalize_source_refs()
- validate_relative_posix_path()
location:
- archledger/source_refs.py
fulfilled_requirements: []
risks: []
tags: []
body_format: markdown
created_at: '2026-05-21T11:32:28Z'
updated_at: '2026-05-21T11:32:28Z'
source_refs:
- archledger/source_refs.py
---

The `source_refs.py` module handles validation and normalization of source traceability links on architecture records. `validate_relative_posix_path()` enforces that source ref paths are relative, use POSIX separators, and do not traverse parent directories. `normalize_source_refs()` processes the raw `source_refs` list from YAML front matter, supporting both shorthand string syntax (`path/to/file.py#SymbolName`) and full mapping syntax with explicit path, symbols, and reason. It verifies that referenced paths and directories actually exist in the workspace. `RelativePosixPathError` provides structured error reporting for invalid paths. This module was extracted from `model.py` to keep source ref validation independent from the core data model.
