# Configuration

Stable configuration lives in `.ledger/arch/config.toml`. Shared project identity and topology live in `.ledger/ledger.toml`. Authoritative Archledger data is `.ledger/arch/archledger` through a Ledgercore repository mount. Root-level configs and `archledger_dir` are migration-only input.

## Important sections

- `[source]` controls the canonical source dialect and extensions.
- `[ids]` controls ledger ID prefix/width and optional ID segment behavior.
- `[build]` controls default output behavior and converter selection.
- `[tracking]` controls workspace snapshots and change detection.
- `[arc42]` controls document metadata defaults.
- `[skill]` points agents at the repository skill file.

## Example

```{code-block} toml
config_version = 11

[ledger]
code = "al"
name = "archledger"

[ids]
width = 4

[ids.kind_map]
requirement = "content"
risk = "risk"

[source]
format = "markdown"
section_extension = ".md"
record_extension = ".md"
schema_version = 2

[build]
default_output = "architecture.md"
default_format = "markdown"
default_output_dir = "build"
converter = "auto"

[tracking]
enabled = true
state_file = "source-state.json"
scanner = "auto"
```

`[build].default_output_dir` is relative to the project root. Profile sections and tracking state are relative to the Archledger data root.

`source-state.json` stores SHA-256 content hashes only for files. It does not
persist mtimes or file sizes. Directory hashes are derived from file hashes.

The archive path is fixed at `.ledger/arch/archledger/archive` and is used by
`archledger archive` and `archledger doctor --repair` to preserve
ledger-number history without renumbering.

## ID segment modes

`segment_mode = "none"`
IDs use `<prefix>_<number>` (for example `al_0013`).

`segment_mode = "type"`
IDs use `<prefix>_<segment>_<number>` (for example `al_risk_0014`).

Segment resolution order is deterministic:

1. `id_segment` metadata on the record
2. `[ids.segment_map]` by record `type`
3. `default_segment`

The numeric ledger sequence remains global across all segments.

## Per-output overrides

Use `[build.outputs.<format>]` for format-specific settings. Supported keys are
`tool`, `pdf_engine`, `reference_docx`, and `enabled`.
