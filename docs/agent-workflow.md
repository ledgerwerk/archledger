# Agent workflow

Use this workflow when an agent is updating Archledger-managed architecture records.

## Independent preflight

Run these commands independently instead of chaining them with `&&`, because `check` may intentionally fail and should not block later diagnostics:

1. `archledger --json paths`
2. `archledger --json status`
3. `archledger --json check`

For machine extraction from either success or failure payloads:

```bash
archledger --json check | jq '(.result // .error.details) | {errors, warnings}'
```

## Migration branch

If `check` reports legacy IDs or legacy timestamp metadata:

```bash
archledger --json migrate ids --to ledgercore
archledger --json migrate metadata --to versioned
```

Apply the migrations only after the surrounding change is approved:

```bash
archledger --json migrate ids --to ledgercore --apply
archledger --json migrate metadata --to versioned --apply
```

Re-run `archledger --json check` before content edits.

## Impact and context

For broad refreshes:

1. `archledger --json source changed`
2. `archledger --json read --body --include-drafts`

Prefer narrower reads when possible:

- `archledger --json context --changed`
- `archledger --json context --for-file PATH`
- `archledger --json trace RECORD_ID`
- `archledger --json read --section SECTION --body`
- `archledger --json read --kind KIND --body`

## Mutation rules

- Edit only source fragments under `.ledger/arch/archledger/profiles/arc42/sections` and `.ledger/arch/archledger/records`.
- Prefer Archledger mutation commands so record versions stay consistent.
- Use `archledger record body set RECORD_ID --from-file /tmp/body.md` for substantial body updates.
- For list or object metadata, use `--json-value`.
- For raw strings that begin with option-like prefixes such as `--json`, use `--string-value`.
- Do not pass semicolon-delimited strings to list-valued fields.
- Do not mutate archived records merely to silence live completeness warnings.

## Record creation

IDs use one ledger-wide numeric sequence. Do not predict the next ID. Capture the returned `result.id` from:

```bash
archledger --json new KIND "Title"
```

## Final gates

Before finalizing updates:

1. `archledger --json check --strict`
2. `archledger --json source changed --fail-on-unlinked`
3. Run project-specific tests that validate the documented boundaries.
4. Build only when the user needs an exported artifact.
5. Run `archledger --json source snapshot --reason after-archledger-update` after updates are validated.

## Rules

- Treat the fragment tree as the source of truth.
- Do not edit generated build output as source.
- Add `source_refs` when a fragment describes concrete implementation artifacts.
- Keep external references generic; Archledger stores links but does not resolve external semantics.
