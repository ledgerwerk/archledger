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

`archledger` is a dual-source ledger:

- Markdown and AsciiDoc are both first-class source formats.
- The source fragments under the configured `archledger_dir` are the source of truth.
- Generated build output under the configured build output directory is derived only.
- Native same-format builds require no external converters.

## Never do these things

- Do not edit generated build output as canonical source.
- Do not require `archledger build` before understanding the current documentation state.
- Do not describe Markdown projects as legacy unless the user explicitly asks about an older migration path.
- Do not migrate source dialects unless the user explicitly asks for `source convert`.
- Do not invent architecture facts without repository evidence.
- Do not leave placeholder bodies in accepted records.
- Do not treat `.feature` files as canonical source; archledger records are the source of truth.
- Do not run Cucumber or any BDD runner from archledger; automation commands are stored but never executed.

## Fresh-context entry protocol

For SDD-enabled projects, prefer these compact entry points:

```text
archledger context --for-file PATH
archledger context --for-record RECORD_ID
archledger context --changed
archledger trace RECORD_ID
archledger sdd status
archledger sdd check --strict
```

````

### BDD / Gherkin

BDD is **metadata on existing records** (``runtime_scenario``, ``quality_scenario``).  Gherkin ``.feature`` files are imported/exported artifacts; archledger does **not** run Cucumber or any BDD runner.

```bash
# Import a feature file as behavior records
archledger bdd import tests/bdd/features/lifecycle.feature \
  --kind runtime-scenario --status proposed

# Export a record as a .feature file
archledger bdd export al_runtime_0123 \
  --out tests/bdd/features/lifecycle.feature
````

Imported records carry a `bdd` front-matter block (feature, rule, scenario, tags, given/when/then, automation) and a `source_refs` entry with role `documents` linking to the originating feature file. Use `source_refs` and `test_refs` to bind features, tests, and code for drift detection.

Use `archledger --json read --body` as the agent source of truth; the `.feature` file is a derived artifact.

Use `record set`, `record meta set`, `record body append`, `refs add`,
`links add`, and `ac add` instead of hand-editing front matter when the
requested mutation maps to one of those commands.

When the user asks to update existing archledger content, detect source drift first:

```bash
archledger --json source changed
```

Then read current archledger source state directly:

```bash
archledger --json paths
archledger --json status
archledger --json check
archledger --json read --body --include-drafts
```

Then:

1. Treat the returned source fragments as the current architecture truth.
2. Treat `changed` output as the default scope filter for which source files and architecture fragments to inspect.
3. Use generated exports only as disposable deliverables.
4. Use `archledger build --format markdown` or `archledger build --format asciidoc` for native validation.
5. Do not read generated build output from the configured build output directory as source of truth.
6. Read `archledger.toml` `[ids]` settings before creating, validating, or rewriting ledger ID references.
7. Respect `[ids].segment_mode`:
   - `none`: `<prefix>_<number>`
   - `type`: `<prefix>_<segment>_<number>` with segment from `id_segment`, `ids.segment_map[type]`, or `ids.default_segment`.

If storage is missing and the user asked to create architecture docs in this repository:

```bash
archledger init --source-format markdown
# or
archledger init --source-format asciidoc
```

If the user wants starter content:

```bash
archledger seed arc42-minimal
```

## Record authoring protocol

Use the CLI to allocate ids and paths, then edit the generated source fragment whose dialect matches `source.format`.

```bash
archledger new requirement --title "Render architecture document from source fragments" --status proposed
archledger new white-box --title "Overall System" --status proposed
archledger new black-box --title "CLI" --parent al_0013 --status proposed
archledger new adr --title "Treat source fragments as canonical" --status proposed
archledger new quality-requirement --title "Deterministic native builds" --status proposed
```

Every section file and record file must keep YAML front matter followed by a body in the configured dialect. Common metadata:

```yaml
schema_version: 2
id: al_0014
type: black_box
title: "CLI"
status: proposed
section: building_block_view
order: 10
date: "2026-05-20"
body_format: markdown
created_at: "2026-05-20T00:00:00Z"
updated_at: "2026-05-20T00:00:00Z"
```

`body_format` must match the project source format (`markdown` or `asciidoc`).
Ledger IDs must match the configured `[ids]` format in `archledger.toml`; do not hardcode `al_` in automation.

When a fragment documents concrete implementation artifacts, add optional `source_refs` metadata:

```yaml
source_refs:
  - archledger/repository.py#ArchitectureRepository
  - path: archledger/storage/project_config.py
    symbols:
      - ProjectConfig
    reason: "Tracking configuration contract"
  - path: archledger/templates/
    reason: "Directory-wide template ownership"
```

Rules:

- paths are relative to the workspace root
- directory refs end with `/`
- use `changed` output to identify unlinked changed files and add `source_refs` where traceability is useful

### Creating diagrams

Use diagram records for visual architecture views:

```bash
archledger new diagram "Runtime login flow" --section runtime_view --status proposed
archledger new diagram "Deployment topology" --section deployment_view
archledger new diagram "Login sequence" --diagram-type mermaid
```

Diagram records default to `diagram_type = "text"`. Dense architecture decomposition
diagrams should use `text` or `unicode` so they remain readable in source, Git diffs,
terminal output, and native builds. Prefer Mermaid only for compact sequence, state,
or flow diagrams.

Diagram syntax by source format and type:

- Markdown text/ascii/unicode: fenced ` ```textdiagram ` blocks
- Markdown svgbob: fenced ` ```svgbob ` blocks
- Markdown mermaid: fenced ` ```mermaid ` blocks
- AsciiDoc text/ascii/unicode: `[source,text]` + `----` blocks
- AsciiDoc svgbob: `[svgbob]` + `....` blocks
- AsciiDoc mermaid: `[mermaid]` + `....` blocks

Supported `--diagram-type` values: `text` (default), `ascii`, `unicode`, `svgbob`, `mermaid`.

Prefer sections:

- `context_and_scope` for context diagrams
- `building_block_view` for structure/decomposition
- `runtime_view` for flows/sequences
- `deployment_view` for topology
- `cross_cutting_concepts` for shared mechanisms

## Reading and editing rules

- Prefer `archledger --json source changed` before broad repository reads when the user wants architecture docs refreshed.
- Always run `archledger --json source changed` before refreshing architecture docs unless the user only asked to inspect a single known record.
- Prefer `archledger --json read --body` over `archledger build` when you need the current architecture state.
- Read the repository evidence before writing documentation: README, tests, package metadata, CI, deployment files, and design notes.
- Update section files and record files directly; never patch generated complete documents as the source of truth.
- Never edit generated build output in the configured build output directory; it is derived output only.
- Never delete numbered fragments; use `archledger archive <id> --reason "..."` and repair structural gaps with `archledger doctor --repair`.
- Use `archledger renumber --id-segment-mode type|none --apply` to switch ID shell format while preserving numeric sequence.
- Use `source_refs` when a record or section describes concrete files, symbols, or directories.
- Prefer `proposed` for newly inferred records unless the user explicitly says the content is accepted.
- Run `archledger check` after record edits.
- Build only when the user explicitly asks for an exported artifact or when converter-backed output validation is part of the task.
- Keep assumptions explicit and use `draft` or `proposed` when evidence is incomplete.

## Build and export matrix

Native no-tool builds:

```bash
archledger build --format markdown
archledger build --format asciidoc
```

Optional exports:

- Markdown source -> HTML, DOCX, RST, Textile, PDF, and AsciiDoc through `pandoc`
- AsciiDoc source -> HTML through `asciidoctor`
- AsciiDoc source -> PDF through `asciidoctor-pdf`
- AsciiDoc source -> DOCX, Markdown, RST, and Textile through Asciidoctor DocBook + `pandoc`

## Validation protocol

Before finalizing changes:

```bash
archledger check
archledger build --format markdown
archledger build --format asciidoc
python -m pytest -q
archledger --json source snapshot --reason after-archledger-update
```

Choose the native build that matches the project source format. Use optional export builds only when the user asked for those artifacts or when validating converter-backed formats.
Do not run `snapshot` until the documentation updates have been applied and validated.

For automation, prefer JSON:

```bash
archledger --json source changed
archledger --json check
archledger --json read --body
archledger --json source snapshot --reason after-archledger-update
archledger --json build --format html --format markdown
```

## Content quality bar

Good archledger content is concrete, traceable, and concise:

- what exists
- why it exists
- which repository evidence supports it
- which stakeholder, quality goal, constraint, decision, or risk it affects

Avoid generic filler. Prefer precise source-backed statements over broad architecture boilerplate.
