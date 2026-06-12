---
name: archledger
description: Maintain source-first arc42 architecture documentation backed by Markdown or AsciiDoc records, YAML front matter, validation, drift tracking, and optional exports.
license: Apache-2.0
compatibility: opencode,codex,chatgpt
metadata:
  audience: coding-agents
  workflow: architecture-documentation,arc42
---

# archledger skill

## When to use this skill

Use this skill when a coding agent needs to create, inspect, enrich, repair, or validate architecture documentation managed by `archledger`.

## Ledger boundary

Archledger is an isolated architecture ledger. It stores architecture records, links, and source references. It does not import/export behavior specs, enforce SDD policy, or coordinate external ledgers.

Use Archledger only for architecture context:

- `archledger --json context ...`
- `archledger --json trace ...`
- `archledger --json read ...`
- `archledger --json check`
- `archledger --json source changed`

Do not ask Archledger to import, export, parse, or validate behavior specs. If a record links to an external artifact, preserve the link and leave semantic resolution to an external organizer.

## Core workflow

1. Read current state:
   - `archledger --json paths`
   - `archledger --json status`
   - `archledger --json check`
   - `archledger --json read --body --include-drafts`
2. Detect implementation drift:
   - `archledger --json source changed`
3. Apply focused mutations with:
   - `record set`, `record meta set`, `record body set|append`
   - `refs add`, `links add`, `ac add`
4. Re-run `archledger check`.

## Source and build guidance

- Markdown and AsciiDoc are both first-class source formats.
- Source fragments under the configured `archledger_dir` are canonical.
- Generated build output is derived only.
- Do not edit generated build output as source of truth.

## Validation protocol

Before finalizing updates:

```bash
archledger check
python -m pytest -q
```
