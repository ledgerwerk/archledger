---
schema_version: 2
id: al_block_0114
type: black_box
title: "ID Segment Resolution"
status: proposed
section: building_block_view
level: 1
parent: al_block_0041
order: 165
date: "2026-05-23"
interfaces:
  - id_segment_for_metadata()
  - id_segment_for_record()
  - id_segment_for_new_record()
location:
  - archledger/id_segments.py
fulfilled_requirements: []
risks: []
tags: []
body_format: markdown
created_at: "2026-05-23T11:27:37Z"
updated_at: "2026-05-23T11:27:37Z"
source_refs:
  - archledger/id_segments.py
---

The `id_segments` module resolves content-derived ID segments for segmented ledger IDs. When `segment_mode` is `type`, each record ID includes a segment token derived from the record's type metadata.

Resolution priority:

1. Explicit `id_segment` in the record's front matter metadata.
2. Mapped segment from the configured `segment_map` keyed by record `type`.
3. The configured `default_segment` as fallback.

Three entry points serve different callers: `id_segment_for_metadata()` for raw metadata dicts (used by renumber), `id_segment_for_record()` for loaded `ArchitectureRecord` objects (used by repository), and `id_segment_for_new_record()` for record creation where the kind is known but no record exists yet. All three validate the resolved segment against the `ID_SEGMENT_PATTERN` regex via `validate_id_segment()`.

This module is intentionally thin — it isolates the resolution policy so that `renumber.py` and `repository.py` share the same logic without coupling to each other.
