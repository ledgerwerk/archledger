# archledger

`archledger` is an arc42-oriented architecture documentation ledger that stores canonical source fragments as YAML front matter plus AsciiDoc bodies. It keeps a small project-local `archledger.toml` in the source workspace and stores human-editable section and record sources under a configurable `archledger_dir`.

Use it to keep architecture building blocks, runtime scenarios, deployment notes, cross-cutting concepts, ADRs, quality scenarios, risks, and glossary terms as separate source fragments, then assemble one canonical architecture document and export disposable rendered outputs.

## What archledger is

`archledger` is intentionally small:

- project-local config discovery from `archledger.toml` or `.archledger.toml`
- human-editable AsciiDoc source fragments with YAML front matter
- a compact Typer CLI for initialization, record creation, validation, listing, inspection, migration, and document builds
- deterministic canonical `.adoc` assembly with optional export formats

It is **not** a task tracker, workflow engine, lock manager, or sync tool.

## Install

```bash
python -m pip install -e .
archledger --version
```

Optional export tools:

- HTML: `asciidoctor`
- PDF: `asciidoctor-pdf`
- DOCX / Markdown / reStructuredText / Textile: `asciidoctor` and `pandoc`

## Quick start

```bash
archledger init
archledger new white-box --title "Overall System" --status accepted
archledger new black-box --title "CLI" --parent white_box_0001 --status accepted
archledger new adr --title "Use AsciiDoc fragments with YAML front matter"
archledger check
archledger build
archledger build --format html --output docs/architecture.html
```

Useful supporting commands:

```bash
archledger status
archledger where
archledger list --include-draft
archledger show black_box_0001
archledger seed arc42-minimal
archledger convert-sources --to asciidoc --write
```

## Storage layout

By default, `archledger init` writes `archledger.toml` at the workspace root and stores state under `.archledger/`.

```text
archledger.toml
.archledger/
  storage.yaml
  sections/
    01_introduction_and_goals.adoc
    ...
    12_glossary.adoc
  records/
    requirements/
    building_blocks/
    concepts/
    constraints/
    contexts/
    decisions/
    deployment/
    glossary/
    quality_goals/
    quality_requirements/
    quality_scenarios/
    risks/
    runtime/
    stakeholders/
    strategy/
  build/
    architecture.adoc
    architecture.html
    architecture.pdf
    architecture.docx
    architecture.md
    architecture.rst
    architecture.textile
```

Relative `archledger_dir` values are resolved from the config file directory. Absolute paths are used as-is, so external state directories work without creating a nested `.archledger/` inside them.

## Canonical source format

Canonical source fragments use YAML front matter plus AsciiDoc body content:

```adoc
---
schema_version: 2
id: adr0001
type: adr
title: "Use AsciiDoc fragments with YAML front matter"
status: accepted
section: architecture_decisions
order: 10
date: "2026-05-20"
deciders:
  - Holger
supersedes: []
related: []
tags: []
body_format: asciidoc
created_at: "2026-05-20T00:00:00Z"
updated_at: "2026-05-20T00:00:00Z"
---

[discrete]
=== Context

What problem or force caused this decision?

[discrete]
=== Decision

What was decided?
```

Generated build outputs are disposable artifacts. The canonical source of truth stays in the individual section and record fragments.

## Build output

`archledger build` always assembles a canonical `.adoc` document for AsciiDoc-backed projects, then optionally exports additional formats:

```bash
archledger build
archledger build --format asciidoc
archledger build --format html
archledger build --format pdf
archledger build --format docx
archledger build --format markdown
archledger build --formats html,markdown
archledger build --all
archledger --json build --formats html,markdown
```

For DOCX, Markdown, reStructuredText, and Textile exports, `archledger` first renders a DocBook intermediate with `asciidoctor` and then converts that intermediate with `pandoc`.

Format resolution rules:

- `--format` builds one explicit format.
- `--formats` builds a comma-separated set of formats.
- `--all` builds every supported export format.
- If `--format` is omitted and `--output` has a known extension, `archledger` infers the output format from the extension.
- If neither is provided, `archledger` uses the configured default format.

Legacy Markdown-backed projects still build Markdown output. Migrate them explicitly with:

```bash
archledger convert-sources --to asciidoc --write
archledger build --format asciidoc
```

## Agent skill

The repository-provided agent protocol lives at `skills/archledger/SKILL.md`.
It is repository content for coding agents, not packaged Python data. Agents
should prefer `archledger --json where`, `archledger --json check`,
`archledger build`, `archledger convert-sources`, and `archledger seed arc42-minimal`
when bootstrapping or updating architecture documentation.

## Agent guidance

- Prefer `--json` for automation and agent workflows.
- Edit `.adoc` source fragments, not generated build artifacts.
- Use `archledger check` before `archledger build` when mutating records programmatically.
- Treat Markdown projects as legacy source and migrate them explicitly instead of silently rewriting them.
- Keep `.archledger/` out of version control unless you intentionally want state inside the repository. The default pattern is to commit `archledger.toml` and ignore `.archledger/`.
