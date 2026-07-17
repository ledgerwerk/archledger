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

If a record links to an external artifact, preserve the link and leave semantic resolution to an external organizer.

## Workflow

### Phase 1: independent preflight

Run these commands independently rather than chaining them with `&&`, because `check` may intentionally fail and should not block later diagnostics:

```bash
archledger --json paths
archledger --json status
archledger --json check
```

For machine extraction from either a successful or failed check payload:

```bash
archledger --json check | jq '(.result // .error.details) | {errors, warnings}'
```

### Phase 2: migration branch

When findings report legacy IDs or legacy timestamp metadata, inspect the dry runs first:

```bash
archledger --json migrate ids --to ledgercore
archledger --json migrate metadata --to versioned
```

Apply them only after the surrounding task or change plan is approved:

```bash
archledger --json migrate ids --to ledgercore --apply
archledger --json migrate metadata --to versioned --apply
```

Re-run `archledger --json check` before content edits.

### Phase 3: impact and context

For broad refreshes:

```bash
archledger --json source changed
archledger --json read --body --include-drafts
```

Prefer narrower reads when possible:

```bash
archledger --json context --changed
archledger --json context --for-file PATH
archledger --json trace RECORD_ID
archledger --json read --section SECTION --body
archledger --json read --kind KIND --body
```

### Phase 4: mutation

Prefer Archledger mutation commands so record versions stay consistent.

For typed metadata:

```bash
archledger record meta set RECORD_ID KEY VALUE
archledger record meta set RECORD_ID KEY --json-value '["item"]'
archledger record meta set RECORD_ID KEY --string-value "--json envelopes are supported"
archledger record meta set RECORD_ID KEY --from-file values.yaml
```

Use `--json-value` for lists and objects. Do not pass semicolon-delimited strings to list-valued fields. For substantial bodies:

```bash
archledger record body set RECORD_ID --from-file /tmp/body.md
```

### Phase 5: record creation

IDs use one ledger-wide numeric sequence. Never predict record IDs. Capture the actual `result.id` returned by `new`:

```bash
archledger --json new concept "Implementation workspace snapshot"
```

### Phase 6: final gates

```bash
archledger --json check --strict
archledger --json source changed --fail-on-unlinked
```

Run project-specific tests that validate the documented boundaries. Build only when an exported artifact is requested or is a committed project deliverable:

```bash
archledger build --output ARCHITECTURE.md
```

After validation passes, record the final snapshot explicitly:

```bash
archledger --json source snapshot --reason after-archledger-update
```

## Rules

- Never predict record IDs.
- Capture `result.id` from `new` before referring to the new record again.
- Never pass a semicolon string to a list-valued field.
- Never edit generated output as source of truth.
- Never mutate archived records merely to silence live-content warnings.
- Prefer CLI mutations so Archledger controls version increments.
- If raw source editing is unavoidable, increment `version` exactly once for the logical change and run strict validation.
- Keep Archledger isolated from behavior-spec and organizer semantics.
- Do not auto-snapshot unresolved drift.

## Canonical repository storage

Current Archledger projects use only the Ledgercore repository mount:

```text
shared identity and topology: .ledger/ledger.toml
stable settings:              .ledger/arch/config.toml
authoritative data:            .ledger/arch/archledger
```

Do not use `archledger.toml`, `.archledger.toml`, `.archledger/`, `archledger_dir`, sibling-ledger storage, or arbitrary external roots as normal runtime configuration. Legacy layouts require explicit inspection and apply:

```bash
archledger --json migrate project
archledger --json migrate project --apply
```

Migration inspection is read-only. Apply backs up before writes, stages below `.ledger/arch`, verifies before activation, preserves the source by default, and never invokes Git.
