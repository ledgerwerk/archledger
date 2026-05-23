---
schema_version: 2
id: al_block_0112
type: black_box
title: "ID Utilities"
status: proposed
section: building_block_view
level: 1
parent: al_block_0041
order: 145
date: "2026-05-22"
interfaces:
  - format_ledger_id()
  - parse_ledger_id()
  - is_ledger_id()
  - filename_for_ledger_id()
  - ledger_id_from_filename()
location:
  - archledger/ids.py
fulfilled_requirements: []
risks: []
tags: []
body_format: markdown
created_at: "2026-05-22T21:47:42Z"
updated_at: "2026-05-22T21:47:42Z"
source_refs:
  - archledger/ids.py
  - tests/test_ids.py
---

The `ids` module provides centralized ledger ID handling functions: `format_ledger_id()` converts an integer to the `al_NNNN` string format, `parse_ledger_id()` extracts the numeric part, `is_ledger_id()` validates a string, and `filename_for_ledger_id()` / `ledger_id_from_filename()` convert between IDs and filenames. These utilities were extracted from `storage/meta.py` and `storage/paths.py` to provide a single source of truth for ID format rules (`al_` prefix, 4-digit zero-padded number).
