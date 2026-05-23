---
schema_version: 2
id: al_runtime_0118
type: runtime_scenario
title: "Renumber ledger IDs"
status: proposed
section: runtime_view
order: 60
date: "2026-05-23"
participants:
  - CLI Layer
  - Renumber Service
  - ID Segment Resolution
  - Config Layer
  - Storage Layer
trigger: User invokes `archledger renumber` with optional prefix/width/segment-mode options
result: All source files renamed and rewritten with new ID format, config and storage metadata updated
body_format: markdown
created_at: "2026-05-23T11:28:33Z"
updated_at: "2026-05-23T11:28:33Z"
source_refs:
  - archledger/cli.py
  - archledger/renumber.py
  - tests/test_renumber_cli.py
---

1. User invokes `archledger renumber --id-prefix <new>` and/or `--id-width <n>` and/or `--id-segment-mode <mode>`.
2. CLI validates options and delegates to `renumber_project()` in `renumber.py`.
3. The renumber service collects all numbered source files from sections, records, and archive directories, parsing each with the current `LedgerIdFormat`.
4. For each file, it computes the new ID using the new format and segment resolution from `id_segments.py`.
5. It builds a rename plan and a rewrite plan (finding all ID references across all source files).
6. It validates no duplicate source IDs and no target collisions.
7. Without `--apply`: returns the plan as JSON or formatted text and exits.
8. With `--apply`: rewrites file contents, renames files via two-phase temp strategy, updates `archledger.toml`, and recomputes `storage.yaml`.
9. CLI outputs the summary of renamed files and rewritten references.
