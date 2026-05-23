---
schema_version: 2
id: al_adr_0116
type: adr
title: "Renumber command is dry-run by default"
status: proposed
section: architecture_decisions
order: 130
date: "2026-05-23"
deciders:
  - archledger maintainers
supersedes: []
related: []
tags: []
body_format: markdown
created_at: "2026-05-23T11:27:58Z"
updated_at: "2026-05-23T11:27:58Z"
---

## Context

Changing ledger ID format (prefix, width, or segment mode) is a destructive operation that touches every source file in the `.archledger/` directory. File renames, reference rewrites, and config mutations cannot be trivially undone. Users need a safe way to preview changes before committing.

## Decision

The `archledger renumber` command is dry-run by default. It computes the full rename and rewrite plan and reports what would change, without modifying any files. The `--apply` flag is required to execute the plan.

When `--apply` is used, the renumber service:

1. Validates the plan (no duplicate source IDs, no target collisions).
2. Rewrites file contents (replacing all ID references).
3. Renames files via a two-phase temp-file strategy to avoid overwriting in-place.
4. Updates `archledger.toml` with the new format settings.
5. Recomputes `storage.yaml` counter.

## Consequences

- Users can safely experiment with `archledger renumber --id-prefix foo` and review the plan.
- The `--apply` flag makes the destructive nature of the operation explicit.
- JSON output includes full details of planned renames and rewrites for programmatic review.

## Alternatives considered

- Apply by default with `--dry-run`: rejected because the safer convention (default no-op) reduces accident risk.
- Interactive confirmation: rejected because the CLI is designed for both human and agent use; a flag is more machine-friendly.
