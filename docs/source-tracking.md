# Source tracking

## Snapshots

`snapshot` stores a baseline of the tracked workspace files:

```{code-block} bash
archledger --json source snapshot --reason after-archledger-update
```
`source-state.json` stores a monotonic snapshot `version` and SHA-256
content hashes only for files. It does not persist timestamps, mtimes, or file
sizes. Directory hashes are derived from file hashes after scanning.

## Changes

`changed` compares the current workspace against the stored baseline:

```{code-block} bash
archledger --json source changed
archledger --json source changed --include-drafts
```
Results report baseline and current versions rather than scan dates.

If `[tracking].enabled = false`, both commands fail explicitly instead of
creating or reading misleading tracking state.

## Linking source_refs

When a fragment documents concrete implementation artifacts, add `source_refs`
that point at relative workspace paths:

```{code-block} yaml
source_refs:
  - archledger/repository.py#ArchitectureRepository
  - path: archledger/storage/project_config.py
    symbols:
      - ProjectConfig
      - load_project_config
    reason: "Tracking configuration validation"
  - path: archledger/templates/
    reason: "Bundled templates"
```
Use POSIX separators, keep the paths relative to the workspace root, and end
directory references with `/`.

## Recommended workflow

Use tracking as a repeatable drift loop instead of a one-off report:

```{code-block} bash
archledger --json source changed
archledger --json read --body --include-drafts
archledger --json check
archledger --json source snapshot --reason after-archledger-update
```
In practice:

1. Add `source_refs` when a fragment describes real code, configuration, or directories.
2. Run `changed` to see what moved since the last accepted baseline.
3. Update only the impacted fragments and validate them with `check`.
4. Record a fresh snapshot after the documentation update is complete.
