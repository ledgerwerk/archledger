---
schema_version: 2
id: al_block_0113
type: black_box
title: "Renumber Service"
status: proposed
section: building_block_view
level: 1
parent: al_block_0041
order: 155
date: "2026-05-23"
interfaces:
  - renumber_project()
location:
  - archledger/renumber.py
fulfilled_requirements: []
risks: []
tags: []
body_format: markdown
created_at: "2026-05-23T11:27:28Z"
updated_at: "2026-05-23T11:27:28Z"
source_refs:
  - archledger/renumber.py
  - tests/test_renumber_cli.py
---

The `renumber` module provides the `renumber_project()` service that replans and optionally applies changes to the ledger ID format across all source files. It supports changing the ID prefix, width, and segment mode.

The renumber workflow operates in two phases: first it builds a rename plan (collecting numbered paths, computing new IDs via the configured `LedgerIdFormat` and segment resolution) and a rewrite plan (finding and replacing all ID references in source files). Then, if `apply=True`, it atomically rewrites file contents, renames files via a two-phase temp-file strategy to avoid collisions, updates `archledger.toml` with the new ID format settings, and recomputes `storage.yaml` counters.

When `apply=False` (dry-run, the default), it validates the plan and returns the computed changes without modifying any files. The CLI `renumber` command delegates to this service and formats the result for human or JSON output.

Key data structures: `RenumberResult` (top-level result with old/new format, renamed paths, rewritten files), `RenumberedPath` (old/new ID and path pair), and `RewrittenFile` (path with replacement count).
