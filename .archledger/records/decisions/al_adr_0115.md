---
schema_version: 2
id: al_adr_0115
type: adr
title: "Config v7 adds configurable ID prefix, width, and segment mode"
status: proposed
section: architecture_decisions
order: 120
date: "2026-05-23"
deciders:
  - archledger maintainers
supersedes: []
related: []
tags: []
body_format: markdown
created_at: "2026-05-23T11:27:42Z"
updated_at: "2026-05-23T11:27:42Z"
---

## Context

Config v5 hardcoded the ID format as `al_` prefix with 4-digit zero-padded numbers. Projects that manage multiple architecture ledgers (e.g., monorepos with independent sub-project docs) need distinct ID prefixes to avoid confusion when records from different projects appear in the same search or review. Some projects also want wider numbers or a different prefix.

Task-0019 (flexible IDs renumbering) introduced configurable prefix and width. Task-0020 (content segment IDs) added segment mode support. The config schema needed to evolve to persist these settings.

## Decision

Config version 7 adds an `[ids]` section with:

- `prefix` (default: `al`) — 2–16 lowercase alphanumeric characters, must start with a letter.
- `width` (default: `4`) — minimum digit count, range 2–12.
- `segment_mode` (default: `none`) — either `none` for unsegmented `al_NNNN` IDs or `type` for segmented `al_<segment>_NNNN` IDs.
- `default_segment` (default: empty) — fallback segment token when `segment_mode=type`.
- `segment_map` (default: empty dict) — maps record types to segment tokens.

The `init` command accepts `--id-prefix`, `--id-width`, and `--id-segment-mode` options to set these at project creation. `LedgerIdFormat` in `ids.py` is the single source of truth for parsing and formatting IDs according to the configured settings.

## Consequences

- Projects can now use distinct ID prefixes and widths. The `renumber` command migrates existing projects.
- Default behavior is unchanged: new projects still get `al_0001`-style IDs.
- Config files with no `[ids]` section fall back to defaults, so existing projects are forward-compatible.
- Bumping config version to 7 signals the new fields; migration layer handles older configs.

## Alternatives considered

- Separate ID format file: rejected because it would add a new file for a small set of fields that belong alongside other project configuration.
- Hardcoded prefix/width only: rejected because it would not support multi-project disambiguation or type-derived segments.
