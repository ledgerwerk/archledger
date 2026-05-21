# archledger

`archledger` is an arc42-oriented architecture documentation ledger. It stores architecture knowledge as small, reviewable source fragments with YAML front matter and Markdown or AsciiDoc bodies. The fragments are the source of truth; complete documents are generated artifacts written to the configured build output directory (by default `.archledger/build/`).

## Release status

`archledger` is currently **beta**.

- Native Markdown and AsciiDoc source workflows are the most stable path.
- Converter-backed exports are supported when the required external tools are installed and validated by CI.
- See `CHANGELOG.md` for recent release-oriented changes and `docs/release-process.rst` for the maintainer release checklist.

## What archledger is

`archledger` is intentionally small:

- project-local config discovery from `archledger.toml` or `.archledger.toml`
- canonical source fragments in Markdown or AsciiDoc
- a compact Typer CLI for init, read, record creation, validation, source drift tracking, migration, and builds
- deterministic native document assembly with optional converter-backed exports

It is **not** a task tracker, workflow engine, lock manager, or sync service.

## When to use it

Use `archledger` when you want architecture documentation that can be updated incrementally by humans or coding agents, reviewed in Git, and assembled into arc42-style documents on demand.

## Install

Editable development install:

```bash
python -m pip install -e ".[dev]"
```

Normal user install:

```bash
python -m pip install .
```

Docs build support:

```bash
python -m pip install -e ".[docs]"
```

Optional converter tools:

- `pandoc` for Markdown-source exports and some AsciiDoc exports
- `asciidoctor` for native AsciiDoc HTML and DocBook conversion
- `asciidoctor-pdf` for native AsciiDoc PDF output

Converter-backed formats are part of the supported workflow only when those tools are present and the related integration checks pass.

## Quick start

### Markdown source

```bash
archledger init --source-format markdown
archledger seed arc42-minimal
archledger --json read --include-body
archledger build --format markdown
```

### AsciiDoc source

```bash
archledger init --source-format asciidoc
archledger seed arc42-minimal
archledger --json read --include-body
archledger build --format asciidoc
```

## Core concepts

### Workspace config

By default, `archledger init` writes `archledger.toml` at the workspace root and stores state under `.archledger/`. Relative `archledger_dir` values are resolved from the config file location, and `[build].default_output_dir` is resolved relative to that same config directory / workspace root.

### Source fragments

Each section file and record file has YAML front matter plus a body in the configured dialect. Example:

```yaml
---
schema_version: 2
id: adr0001
type: adr
title: "Treat source fragments as canonical"
status: accepted
section: architecture_decisions
order: 10
date: "2026-05-20"
body_format: markdown
created_at: "2026-05-20T00:00:00Z"
updated_at: "2026-05-20T00:00:00Z"
---
```

`body_format` must match the project `source.format` unless you explicitly use the migration escape hatch during a manual source conversion.

### Sections and records

Sections are the arc42 chapter skeleton. Records hold individual requirements, decisions, building blocks, risks, and other architecture facts. Use the CLI to allocate paths and ids, then edit the generated fragment.

### Generated outputs

Generated output files are not canonical source. By default they live under `.archledger/build/`, but `[build].default_output_dir` can move them elsewhere under the project root.

### What to commit

For a project that uses `archledger`, commit the canonical source and config:

- `archledger.toml`
- `.archledger/sections/**`
- `.archledger/records/**`
- optionally `.archledger/storage.yaml` if you want deterministic id allocation across machines
- optionally `.archledger/source-state.json` if your team wants a shared drift baseline

Do **not** treat generated build output as canonical source. The default location is `.archledger/build/**`, but the configured build output directory may be elsewhere under the project root. Generated build output and converter intermediates are disposable unless you are intentionally debugging an export issue.

## Record types

| Kind                  | Common aliases        | Default section            |
| --------------------- | --------------------- | -------------------------- |
| `requirement`         | `requirement`         | `introduction_and_goals`   |
| `stakeholder`         | `stakeholder`         | `introduction_and_goals`   |
| `quality_goal`        | `quality-goal`        | `introduction_and_goals`   |
| `constraint`          | `constraint`          | `architecture_constraints` |
| `context_interface`   | `context-interface`   | `context_and_scope`        |
| `strategy_item`       | `strategy-item`       | `solution_strategy`        |
| `white_box`           | `white-box`           | `building_block_view`      |
| `black_box`           | `black-box`           | `building_block_view`      |
| `interface`           | `interface`           | `building_block_view`      |
| `runtime_scenario`    | `runtime`             | `runtime_view`             |
| `infrastructure`      | `infrastructure`      | `deployment_view`          |
| `concept`             | `concept`             | `cross_cutting_concepts`   |
| `adr`                 | `adr`                 | `architecture_decisions`   |
| `quality_requirement` | `quality-requirement` | `quality_requirements`     |
| `quality_scenario`    | `quality-scenario`    | `quality_requirements`     |
| `risk`                | `risk`                | `risks_and_technical_debt` |
| `glossary_term`       | `glossary-term`       | `glossary`                 |

## Reading source without exporting

Use `read` and the JSON commands to inspect the current source state directly:

```bash
archledger --json where
archledger --json status
archledger --json check
archledger --json read --include-body --include-draft
archledger --json read --section building_block_view --include-body
archledger --json read --kind adr --include-body
```

`--json` is a global option. Use `archledger --json read ...`, not `archledger read --json`.

`read` does not call the build pipeline and does not create generated output files.

## Tracking implementation drift

### Snapshots

```bash
archledger --json snapshot --reason after-archledger-update
```

`snapshot` writes `.archledger/source-state.json` by default. Source-state payloads store SHA-256 content hashes only for files, do not persist mtimes or file sizes, and include a derived directory hash map. If `[tracking].enabled = false`, `snapshot` and `changed` fail explicitly instead of silently creating misleading tracking state.

### Changed files

```bash
archledger --json changed
archledger --json changed --include-draft
```

`changed` reports added, modified, deleted, and possible renamed files plus impacted records and sections linked through `source_refs`.

### Linking `source_refs`

When fragments document real code or directories, add `source_refs`:

```yaml
source_refs:
  - archledger/repository.py#ArchitectureRepository
  - path: archledger/storage/project_config.py
    symbols:
      - ProjectConfig
      - load_project_config
    reason: "Tracking configuration contract"
  - path: archledger/templates/
    reason: "Bundled templates"
```

Paths must be relative to the workspace root. Directory refs end with `/` and must point to an existing directory.

### Practical drift workflow

```bash
archledger --json changed
archledger --json read --include-body --include-draft
# update the affected fragments and their source_refs
archledger --json check
archledger --json snapshot --reason after-archledger-update
```

A useful pattern is:

1. Link records to the relevant code or directories with `source_refs`.
2. Run `changed` before broad documentation refreshes.
3. Update only the fragments whose refs were impacted.
4. Record a fresh snapshot only after the documentation update is validated.

## Building output documents

### Native builds

```bash
archledger build --format markdown
archledger build --format asciidoc
```

### Converted builds

```bash
archledger build --format html
archledger build --formats html,markdown
archledger --json build --formats html,markdown
```

### Tooling matrix

| Source format | Output format                           | Tooling                       |
| ------------- | --------------------------------------- | ----------------------------- |
| Markdown      | Markdown                                | none                          |
| AsciiDoc      | AsciiDoc                                | none                          |
| Markdown      | HTML, DOCX, RST, Textile, PDF, AsciiDoc | `pandoc`                      |
| AsciiDoc      | HTML                                    | `asciidoctor` or `pandoc`     |
| AsciiDoc      | PDF                                     | `asciidoctor-pdf` or `pandoc` |
| AsciiDoc      | DOCX, Markdown, RST, Textile            | `asciidoctor` + `pandoc`      |

Per-output overrides live under `[build.outputs.<format>]`. Supported keys are `tool`, `pdf_engine`, `reference_docx`, and `enabled`. Supported tool values are `auto`, `pandoc`, and `asciidoctor`.

## Migrating source dialects

`convert-sources` is a source migration command, not a general build/export command. It currently supports Markdown-source projects to AsciiDoc-source projects only.

Dry-run the migration first:

```bash
archledger convert-sources --to asciidoc
```

Write the migration:

```bash
archledger convert-sources --to asciidoc --write
```

`--write` now requires `pandoc` by default so the migrated `.adoc` files and the resulting `source.format = "asciidoc"` config stay consistent. If you intentionally want a temporary mixed-body migration, use:

```bash
archledger convert-sources --to asciidoc --write --allow-mixed-body-format
```

Use this escape hatch only when you explicitly accept a manual cleanup step. Run the command from a clean VCS state.

## Configuration reference

Example config v5:

```toml
config_version = 5
archledger_dir = ".archledger"
project_uuid = "..."
project_name = "my-project"

[source]
format = "markdown"       # markdown | asciidoc
front_matter = "yaml"
section_extension = ".md" # .md or .adoc
record_extension = ".md"
schema_version = 2

[build]
default_output = "architecture.md"
default_format = "markdown"
default_output_dir = "build"
include_draft = false
include_superseded = false
strict = false
keep_intermediate = false
converter = "auto"        # auto | pandoc | asciidoctor
pdf_engine = ""
reference_docx = ""

[tracking]
enabled = true
state_file = "source-state.json"
scanner = "auto"          # auto | git | filesystem
```

`[build].default_output_dir` is relative to the directory containing `archledger.toml` or `.archledger.toml`.

`source-state.json` stores SHA-256 content hashes only for files. It does not persist mtimes or file sizes. Directory hashes are derived from file hashes.

## CLI reference for agents

For coding agents, prefer this loop:

1. `archledger --json where`
2. `archledger --json changed`
3. `archledger --json read --include-body --include-draft`
4. Edit only source fragments under `archledger_dir/sections` and `archledger_dir/records`
5. `archledger --json check`
6. Build only when the user asks for an exported artifact
7. `archledger --json snapshot --reason after-archledger-update` after the docs have been updated and validated

## Development

Run the standard checks:

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy archledger
python -m sphinx -b html docs docs/_build/html
```

Release-oriented checks:

```bash
rm -rf dist build *.egg-info
python -m build
python -m twine check dist/*
python -m venv /tmp/archledger-wheel-test
/tmp/archledger-wheel-test/bin/python -m pip install dist/*.whl
/tmp/archledger-wheel-test/bin/archledger --version
```

For the full maintainer checklist, see `docs/release-process.rst`.

## Troubleshooting

| Symptom                                           | Cause                                                                 | Fix                                                                                              |
| ------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `No archledger.toml found`                        | Command ran outside a configured workspace.                           | Run from the project tree or pass `--root`.                                                      |
| Draft records missing from builds                 | Drafts are excluded by default.                                       | Use `--include-draft` or promote the record status.                                              |
| Build blocked by warnings                         | `--strict` treats warnings as failures.                               | Fix the warnings or build without `--strict`.                                                    |
| Converter executable not found                    | Requested output needs `pandoc`, `asciidoctor`, or `asciidoctor-pdf`. | Install the required tool or change the per-output converter config.                             |
| `changed` says no baseline found                  | No source snapshot exists yet.                                        | Run `archledger --json snapshot --reason after-archledger-update` after the docs are current.    |
| `snapshot` or `changed` says tracking is disabled | `[tracking].enabled = false`.                                         | Re-enable tracking or avoid tracking commands for that workspace.                                |
| `convert-sources --write` fails without `pandoc`  | Write mode is strict by default.                                      | Install `pandoc` or re-run with `--allow-mixed-body-format` if you accept a manual cleanup step. |

## Skill

The repository-provided coding-agent protocol lives at `skills/archledger/SKILL.md`.

## Security and trust

`archledger` reads local project files and only invokes external converters when you request output formats that need them. It does not sync or send project content anywhere by itself.
