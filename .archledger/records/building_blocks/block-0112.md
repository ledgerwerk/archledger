---
schema_version: 2
id: block-0112
type: black_box
title: ID Utilities
status: proposed
section: building_block_view
level: 1
parent: block-0041
order: 145
date: "2026-05-22"
interfaces:
  - LedgerIdFormat.format()
  - LedgerIdFormat.parse()
  - LedgerIdFormat.parse_parts()
  - LedgerIdFormat.is_id()
  - LedgerIdFormat.pattern()
  - LedgerIdFormat.reference_pattern()
  - format_ledger_id()
  - parse_ledger_id()
  - parse_ledger_id_parts()
  - is_ledger_id()
  - filename_for_ledger_id()
  - ledger_id_from_filename()
  - validate_id_prefix()
  - validate_id_width()
  - validate_id_segment_mode()
  - validate_id_segment()
location:
  - archledger/ids.py
fulfilled_requirements: []
risks: []
tags: []
body_format: markdown
created_at: "2026-05-22T21:47:42Z"
updated_at: "2026-05-23T11:30:00Z"
source_refs:
  - archledger/ids.py
  - tests/test_ids.py
kind: block
---

The `ids` module provides centralized ledger ID handling with configurable prefix, width, and segment mode. The core abstraction is `LedgerIdFormat`, a frozen dataclass that encapsulates the three ID format parameters and exposes methods for formatting, parsing, pattern generation, and validation.

**Unsegmented mode** (`segment_mode=none`, default): IDs follow `<prefix>_<number>` (e.g., `al_0001`). `format(number)` produces the zero-padded string, `parse(id)` extracts the number, and `pattern()`/`reference_pattern()` produce regexes for exact matching and cross-reference detection respectively.

**Segmented mode** (`segment_mode=type`): IDs follow `<prefix>_<segment>_<number>` (e.g., `adr-0077`). `format(number, segment=...)` includes the validated segment token, and `parse_parts()` returns a `ParsedLedgerId` with both `number` and `segment` fields.

Module-level convenience functions (`format_ledger_id`, `parse_ledger_id`, `is_ledger_id`, etc.) accept optional `prefix`, `width`, and `segment_mode` parameters for callers that need ad-hoc format handling. Validators (`validate_id_prefix`, `validate_id_width`, `validate_id_segment_mode`, `validate_id_segment`) enforce format constraints shared across config parsing, CLI validation, and record checks.

The `LedgerIdFormat` instance is constructed from `ProjectConfig.id_format` and threaded through repository, renumber, and check operations as the single source of truth for ID syntax rules.
