# archledger

`archledger` is a Markdown-first architecture documentation ledger for arc42-style documentation. It keeps a small project-local `archledger.toml` in the source workspace and stores human-editable architecture records under a configurable `archledger_dir`.

Use it to keep architecture building blocks, runtime scenarios, deployment notes, cross-cutting concepts, ADRs, quality scenarios, risks, and glossary terms as separate Markdown files with YAML front matter, then render one complete architecture document.

## What archledger is

`archledger` is intentionally small:

- project-local config discovery from `archledger.toml` or `.archledger.toml`
- human-editable Markdown source records with YAML front matter
- a compact Typer CLI for initialization, record creation, validation, listing, inspection, and document rendering
- deterministic arc42-style Markdown builds

It is **not** a task tracker, workflow engine, lock manager, or sync tool.

## Install

```bash
python -m pip install -e .
archledger --version
```

## Quick start

```bash
archledger init
archledger new white-box --title "Overall System" --status accepted
archledger new black-box --title "CLI" --parent white_box_0001 --status accepted
archledger new adr --title "Use Markdown records with YAML front matter"
archledger check
archledger build --output docs/architecture.md
```

Useful supporting commands:

```bash
archledger status
archledger where
archledger list --include-draft
archledger show black_box_0001
```

## Storage layout

By default, `archledger init` writes `archledger.toml` at the workspace root and stores state under `.archledger/`.

```text
archledger.toml
.archledger/
  storage.yaml
  sections/
    01_introduction_and_goals.md
    ...
    12_glossary.md
  records/
    building_blocks/
    concepts/
    constraints/
    contexts/
    decisions/
    deployment/
    glossary/
    quality_goals/
    quality_scenarios/
    risks/
    runtime/
    stakeholders/
  build/
    architecture.md
```

Relative `archledger_dir` values are resolved from the config file directory. Absolute paths are used as-is, so external state directories work without creating a nested `.archledger/` inside them.

## Record examples

Example black box:

```markdown
---
id: black_box_0001
type: black_box
title: "CLI"
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 10
interfaces: []
location:
  - archledger/cli.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-19T00:00:00Z"
updated_at: "2026-05-19T00:00:00Z"
---

Describe the purpose and responsibility of this black box.
```

Example ADR:

```markdown
---
id: adr0001
type: adr
title: "Use Markdown files with YAML front matter as canonical storage"
status: accepted
section: architecture_decisions
order: 10
date: "2026-05-19"
deciders:
  - Holger
supersedes: []
related: []
tags: []
created_at: "2026-05-19T00:00:00Z"
updated_at: "2026-05-19T00:00:00Z"
---

## Context

What problem or force caused this decision?

## Decision

What was decided?
```

## Build output

`archledger build` renders one Markdown document from the stored section files and records:

```bash
archledger build
archledger build --output docs/architecture.md
archledger build --include-draft
archledger --json build --output /tmp/architecture.md
```

The generated file is disposable output. The canonical source of truth stays in the individual Markdown records and section files.

## Agent guidance

- Prefer `--json` for automation and agent workflows.
- Keep source records human-editable; do not treat generated output as canonical.
- Use `archledger check` before `archledger build` when mutating records programmatically.
- Keep `.archledger/` out of version control unless you intentionally want state inside the repository. The default pattern is to commit `archledger.toml` and ignore `.archledger/`.
