---
schema_version: 2
id: black_box_0013
type: black_box
title: Record Type Registry
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 115
date: "2026-05-21"
interfaces:
  - RECORD_TYPES registry
  - CLI_KIND_ALIASES
  - RecordTypeSpec dataclass
location:
  - archledger/record_types.py
fulfilled_requirements: []
risks: []
tags: []
body_format: markdown
created_at: "2026-05-21T11:31:25Z"
updated_at: "2026-05-21T11:31:25Z"
source_refs:
  - archledger/record_types.py
---

The `record_types.py` module is the central registry for all arc42 record types. It defines `RecordTypeSpec`, a frozen dataclass mapping each record kind to its directory name, filename prefix, default section, template basename, CLI aliases, default status/level, and a context factory function. The `RECORD_TYPES` dictionary provides the authoritative lookup. `CLI_KIND_ALIASES` maps alternative names (e.g., `qg` for `quality_goal`) for the CLI. This module was extracted from `model.py` to keep the model focused on data structures while record type configuration lives in one discoverable location.
