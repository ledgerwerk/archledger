---
name: archledger
description: Fill and maintain Markdown- or AsciiDoc-backed arc42 architecture documentation with YAML front matter, direct source reading, validation, and optional exports.
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
- `.archledger/build/*` is derived output only.
- Native same-format builds require no external converters.

## Never do these things

- Do not edit generated build output as canonical source.
- Do not require `archledger build` before understanding the current documentation state.
- Do not describe Markdown projects as legacy unless the user explicitly asks about an older migration path.
- Do not migrate source dialects unless the user explicitly asks for `convert-sources`.
- Do not invent architecture facts without repository evidence.
- Do not leave placeholder bodies in accepted records.

## Fresh-context entry protocol

When the user asks to update existing archledger content, detect source drift first:

```bash
archledger --json changed
```

Then read current archledger source state directly:

```bash
archledger --json where
archledger --json status
archledger --json check
archledger --json read --include-body --include-draft
```

Then:

1. Treat the returned source fragments as the current architecture truth.
2. Treat `changed` output as the default scope filter for which source files and architecture fragments to inspect.
3. Use generated exports only as disposable deliverables.
4. Use `archledger build --format markdown` or `archledger build --format asciidoc` for native validation.
5. Do not read `.archledger/build/*` as source of truth.

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
archledger new black-box --title "CLI" --parent white_box_0001 --status proposed
archledger new adr --title "Treat source fragments as canonical" --status proposed
archledger new quality-requirement --title "Deterministic native builds" --status proposed
```

Every section file and record file must keep YAML front matter followed by a body in the configured dialect. Common metadata:

```yaml
schema_version: 2
id: black_box_0001
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

## Reading and editing rules

- Prefer `archledger --json changed` before broad repository reads when the user wants architecture docs refreshed.
- Prefer `archledger --json read --include-body` over `archledger build` when you need the current architecture state.
- Read the repository evidence before writing documentation: README, tests, package metadata, CI, deployment files, and design notes.
- Update section files and record files directly; never patch generated complete documents as the source of truth.
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
archledger --json snapshot --reason after-archledger-update
```

Choose the native build that matches the project source format. Use optional export builds only when the user asked for those artifacts or when validating converter-backed formats.

For automation, prefer JSON:

```bash
archledger --json changed
archledger --json check
archledger --json read --include-body
archledger --json snapshot --reason after-archledger-update
archledger --json build --formats html,markdown
```

## Content quality bar

Good archledger content is concrete, traceable, and concise:

- what exists
- why it exists
- which repository evidence supports it
- which stakeholder, quality goal, constraint, decision, or risk it affects

Avoid generic filler. Prefer precise source-backed statements over broad architecture boilerplate.
