---
schema_version: 4
id: concept-0119
type: concept
title: Configurable ledger ID format
status: proposed
section: cross_cutting_concepts
order: 60
applies_to:
  - building_block_view
  - runtime_view
  - architecture_decisions
body_format: markdown
source_refs:
  - archledger/ids.py
  - archledger/id_segments.py
  - archledger/config/model.py
kind: concept
version: 1
---

## Concept

Ledger IDs identify architecture records throughout the system. The ID format is configurable per project via the `[ids]` section in `archledger.toml`, but the single global numeric sequence is always preserved.

### Unsegmented mode (default)

Format: `<prefix>_<number>` (e.g., `al_0001`). The prefix defaults to `al` and width to 4 digits. IDs like `al_0042` are valid for any record type.

### Segmented mode (`segment_mode=type`)

Format: `<prefix>_<segment>_<number>` (e.g., `adr-0077`, `block-0042`). The segment is derived from the record's `type` field via the configured `segment_map`, with an explicit `id_segment` override in front matter, falling back to `default_segment`.

### Resolution chain

1. `LedgerIdFormat` in `ids.py` — parses and formats IDs, provides regex patterns for both exact match and cross-reference detection.
2. `id_segments.py` — resolves the segment token for a record, used by repository (record creation) and renumber (migration).
3. `ProjectConfig.id_format` property — exposes the configured `LedgerIdFormat` to all callers.

### Invariants

- Every record has exactly one numeric ID in the global sequence.
- ID numbers are stable across renumber operations (only prefix/width/segment change).
- File names are derived from the full ID string plus the configured source format extension.
- Cross-references in record bodies are rewritten by the renumber service using the `reference_pattern` regex.
