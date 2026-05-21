---
id: black_box_0010
type: black_box
title: Source Tracking Layer
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 90
interfaces:
- scan_workspace()
- diff_source_states()
- resolve_impacts()
location:
- archledger/source_tracking.py
- archledger/storage/source_state.py
fulfilled_requirements: []
risks: []
tags: []
created_at: '2026-05-20T12:00:00Z'
updated_at: '2026-05-20T12:00:00Z'
source_refs:
- archledger/source_tracking.py
- archledger/storage/source_state.py
---

The source tracking module detects changes between a baseline snapshot and the current workspace state. `scan_workspace` enumerates all tracked files using git or filesystem scanning, computes SHA-256 hashes, and records file sizes and mtimes. `diff_source_states` compares two snapshots to produce a `ChangeSet` listing added, modified, and deleted files with possible rename detection. `resolve_impacts` cross-references changed files with architecture record `source_refs` to identify which records and sections are impacted by the changes, and which changed files have no linked records.

The storage sub-module (`storage/source_state.py`) handles JSON serialization and deserialization of the source state, persisted alongside `storage.yaml`.
