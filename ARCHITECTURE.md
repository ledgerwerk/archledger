---
title: "archledger Architecture Documentation"
date: "2026-05-23"
generator: "archledger 0.1.1.dev1+g15fa163cd"
arc42_template_version: "9.0-EN"
---

# archledger Architecture Documentation

Generated from archledger records. Do not edit this generated file directly.

# Introduction and Goals

archledger is a dual-source architecture documentation ledger for arc42-style documents. Both Markdown and AsciiDoc are first-class source formats. The tool keeps project-local configuration (`archledger.toml`) in the source workspace and stores human-editable architecture records as individual files with YAML front matter. The primary output is a rendered document assembled from these records, with optional exports to HTML, PDF, DOCX, RST, and Textile via pandoc or asciidoctor.

The tool targets three stakeholders: developers who document alongside code, architects who maintain the structural vision, and coding agents that automate documentation workflows via the CLI.

## How to update this architecture

Use the source-first maintenance loop:

```bash
archledger source changed --json
archledger read --json --body
archledger new <type> "<title>" --status accepted
archledger check --strict
archledger build
```

Detailed agent guidance lives in `docs/agent-workflow.rst`.

## Requirements Overview

| Title                                                         | Priority | Source                                                | Stakeholders | Quality goals |
| ------------------------------------------------------------- | -------- | ----------------------------------------------------- | ------------ | ------------- |
| Project initialization creates archledger workspace structure | must     | archledger CLI behavior and repository implementation |              |               |
| File-based source model uses editable records                 | must     | archledger CLI behavior and repository implementation |              |               |
| Record creation enforces schema and unique ids                | must     | archledger CLI behavior and repository implementation |              |               |
| Read current architecture model without export                | must     | archledger CLI behavior and repository implementation |              |               |
| Native build requires no external converter tools             | must     | archledger CLI behavior and repository implementation |              |               |
| Multi-format export supports configured converter tools       | must     | archledger CLI behavior and repository implementation |              |               |
| Source tracking reports changes impacts and unlinked files    | must     | archledger CLI behavior and repository implementation |              |               |
| Path safety prevents writes outside allowed roots             | must     | archledger CLI behavior and repository implementation |              |               |
| CLI provides stable machine-readable JSON output              | must     | archledger CLI behavior and repository implementation |              |               |
| Local-first operation requires no network services            | must     | archledger CLI behavior and repository implementation |              |               |

## Quality Goals

| Title           | Priority | Scenario                                                                                                                                                                       |
| --------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Maintainability | 1        | A developer can add a new record type with template, model mapping, and CLI alias in under 30 minutes, touching at most three files.                                           |
| Reproducibility | 1        | Given the same set of accepted records, archledger build produces byte-identical output regardless of the host machine or locale.                                              |
| Traceability    | 1        | Every architecture record links to source evidence (file paths, CLI commands, test names) so that a reviewer can trace any documented decision back to code within two clicks. |

## Stakeholders

| Title        | Contact | Expectations                                                                                                                                                                                                                                     |
| ------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Coding Agent | None    | JSON CLI output for machine parsing, Deterministic builds for CI pipelines, Seed preset for quick bootstrap, Skill file (SKILL.md) for agent protocol                                                                                            |
| Developer    | None    | Simple installation via pip, Clear CLI commands for init, new, check, build, Human-readable Markdown records easy to edit in any text editor                                                                                                     |
| Architect    | None    | Structured arc42 sections with deterministic ordering, ADR records with Context/Decision/Consequences validation, Quality scenarios with measurable response measures, Cross-references between building blocks, ADRs, risks, and glossary terms |

# Architecture Constraints

archledger operates under several technical constraints that shape its architecture: Python 3.10+ as the runtime, Markdown and AsciiDoc as first-class source formats with YAML front matter, filesystem-only storage (no database), Typer as the CLI framework, and optional external converters (pandoc, asciidoctor) for multi-format exports. These constraints keep the tool lightweight, portable, and easy to automate.

- **Typer CLI interface**
  - Impact: All user-facing functionality is exposed through Typer CLI commands. No GUI, no web API, no library-first API.
  - Notes: archledger uses Typer as its CLI framework. The entry point is `archledger.launcher:main`, registered as the `archledger` console script. All commands return either human-readable text or `--json` structured output. This constraint keeps the tool focused on CLI and automation workflows.
- **Markdown or AsciiDoc with YAML front matter as canonical source**
  - Impact: Record files are plain text, diffable in version control, and editable without special tooling. Both Markdown and AsciiDoc are supported as first-class source formats.
  - Notes: Every architecture record is stored as a Markdown or AsciiDoc file with YAML front matter delimited by `---`. The front matter holds machine-readable metadata and the body holds human-readable prose in the configured dialect. No database, binary format, or JSON store is used. The `body_format` field in each record must match the project's configured `source.format`.
- **No GUI or web interface**
  - Impact: All interaction is through the command line. The --json flag is the machine interface for agents.
  - Notes: archledger exposes no GUI or web interface. All user interaction happens through the Typer CLI. This simplifies the architecture and makes automation straightforward, but means users must be comfortable with command-line tools.
- **Python 3.10+ runtime**
  - Impact: All user-facing functionality is exposed through Typer CLI commands. No GUI, no web API.
  - Notes: archledger requires Python >= 3.10, as declared in `pyproject.toml`. This allows the use of modern type hint syntax (`X | Y` unions, `match` statements) while still supporting current Python distributions on Linux and macOS.
- **No external database dependency**
  - Impact: Storage is limited to the local filesystem. No server process, database engine, or cloud service is required.
  - Notes: archledger stores all state as flat files on the local filesystem. The configuration is a TOML file at the project root, records are Markdown files in subdirectories, and metadata is a YAML file. This keeps the dependency footprint small (Typer, PyYAML, Jinja2) and avoids operational complexity.

# Context and Scope

archledger interacts with three external partners: the source repository (reads config and records, writes build output), coding agents (CLI invocations with JSON output), and CI pipelines (exit codes and build artifacts). Optional external converters (pandoc, asciidoctor, asciidoctor-pdf) are invoked as subprocesses for multi-format exports. All communication is local filesystem access, process I/O, or subprocess invocation.

See the [System Context diagram](#diagram-al_diagram_0035) for a visual overview of actors and system boundaries.

## System Context

archledger operates as a local CLI tool. External actors interact through shell invocations. Optional converter tools (pandoc, asciidoctor) are invoked as subprocesses for non-native export formats.

```textdiagram
┌───────────┐  ┌──────────────┐  ┌──────────────┐
│ Developer │  │ Coding Agent │  │ CI Pipeline  │
└─────┬─────┘  └──────┬───────┘  └──────┬───────┘
      │               │                 │
      └───────────────┼─────────────────┘
                      ▼
           ┌─────────────────────┐
           │   archledger CLI    │
           │  (Typer entrypoint) │
           └─────┬─────────┬─────┘
                 │         │
      ┌──────────▼───┐ ┌───▼──────────────┐
      │  Workspace   │ │  Build Output    │
      │ .archledger/ │ │ ARCHITECTURE.md  │
      │  records/    │ │  + exports       │
      └──────────────┘ └───┬──────────┬────┘
                             │          │
                      ┌──────▼───┐ ┌───▼───────────┐
                      │  pandoc  │ │ asciidoctor   │
                      │ optional │ │   optional    │
                      └──────────┘ └──────────────┘
```

**Caption:** archledger system context showing external actors and adjacent systems

## Business Context

- **Project stakeholders** -> Developers, maintainers, and release managers
  - Stakeholders provide architecture requirements, review generated artifacts, and consume release documentation from repository and CI outputs.

## Technical Context

- **Source repository** -> Source repository
  - The source repository hosts the `archledger.toml` config and the architecture record files. archledger reads records from disk and writes the rendered document back to the repository's build directory or a specified output path.
- **Coding agent harness** -> Coding Agent
  - Coding agents (pi, opencode, etc.) invoke archledger through its CLI, passing `--json` for machine-readable output. The agent skill file (`SKILL.md`) provides the protocol for how agents should interact with archledger: locate config, inspect records via `read`, detect changes via `source changed`, create/update in batches via `new`, validate with `check`, render with `build`, and persist baselines with `source snapshot`.
- **CI pipeline** -> CI runner
  - A CI runner can execute `archledger check` to validate record integrity and `archledger build` to produce the rendered document. Non-zero exit codes signal validation failures. The built Markdown can be published as a CI artifact or deployed to a documentation site. The project uses GitHub Actions for CI (`.github/workflows/tests.yml` for test execution, `.github/workflows/codecov.yml` for coverage reporting, `.github/workflows/pre-commit.yml` for linting, and `.github/workflows/python-publish.yml` for PyPI releases).

# Solution Strategy

The fundamental approach is a file-based pipeline: human-editable Markdown or AsciiDoc records with YAML front matter are stored in a configurable directory, validated by a check command, assembled into a single arc42-style document by a Jinja2-based render step, and optionally converted to other formats (HTML, PDF, DOCX, RST, Textile) via pandoc or asciidoctor. A dialect abstraction (`dialects.py`) ensures that rendering logic works identically for both source formats. The CLI provides the sole interface. No server, database, or GUI is involved.

A source tracking subsystem (`source snapshot`/`source changed`) allows agents to detect which source files changed since the last baseline and which architecture records are impacted via `source_refs` linkage.

The build pipeline is visualized in the [Build Pipeline Flow diagram](#diagram-al_diagram_0059) in the runtime view.

## Strategy Items

## File-based record pipeline with dual-source and multi-format export

**Drivers:** Maintainability, Traceability, Reproducibility
**Constraints:** Markdown or AsciiDoc with YAML front matter as canonical source, No external database dependency, Typer CLI interface
**Related ADRs:** al_adr_0077, al_adr_0078, al_adr_0079

## Strategy

The core approach is a four-stage pipeline: author (create/edit Markdown or AsciiDoc records), validate (check integrity and completeness), assemble (render a single document using dialect-aware templates), and export (convert to requested formats via pandoc or asciidoctor). A source tracking subsystem enables change detection and impact analysis. A migration path allows converting from one source dialect to another. Each stage is independent and stateless except for the shared filesystem. The CLI orchestrates the pipeline and the Repository implements the business logic.

## Trade-offs

- Positive: simple mental model, easy to automate, no server dependency, supports both major documentation formats.
- Negative: no concurrent write protection, no real-time collaboration, referential integrity only checked on demand, external converter dependency for non-native formats.

# Building Block View

The system is decomposed into fifteen black boxes within a single white box. The CLI Layer receives user input and delegates output formatting, the Config Layer parses and renders project configuration, the Repository Layer orchestrates business logic, the Model Layer defines core data structures and validation, the Record Type Registry maps record types to templates and defaults, the Check Layer validates record content per type, the Source Ref Validation layer normalizes traceability links, the Storage Layer handles file I/O, the Assembly Layer renders the document via Jinja2 templates, the Dialect Layer abstracts format-specific markup, the Section Rendering Layer handles per-record-type output, the Render Layer orchestrates the build pipeline, the Converter Layer handles multi-format export, the Source Tracking Layer detects changes and impacts, and the Migration Layer converts between source dialects.

See the [Building Block Layer Structure diagram](#diagram-al_diagram_0040) for a visual decomposition showing the layer relationships.

## Building Block Layer Structure

The system is organized as a layered pipeline. User input flows down from the
CLI through business logic to storage. Rendering flows upward from storage
through assembly to the build output.

```textdiagram
┌─ Interface ──────────────────────────────────────────────────┐
│  CLI Layer  (cli.py, cli_formatting.py, cli_payloads.py)    │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Business Logic ────────────────────────────────────────────┐
│  Repository (repo.py)        Model (model.py)               │
│  Record Types (rec_types)    Checks (checks.py)             │
│  Source Refs (source_refs.py)                               │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Configuration ────────────────────────────────────────────┐
│  Config Layer (config/)                                    │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Rendering ────────────────────────────────────────────────┐
│  Render (render.py)       Assembly (assembly.py)           │
│  Dialect (dialects.py)    Section Rendering                │
│                           (section_rendering.py)            │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Export ───────────────────────────────────────────────────┐
│  Converter (converters, conversion_plan, formats)          │
│  Migration (migration.py)                                  │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Infrastructure ───────────────────────────────────────────┐
│  Storage (storage/)         Source Tracking                 │
│                             (source_tracking.py)            │
└────────────────────────────────────────────────────────────┘
```

**Caption:** Layered decomposition of archledger building blocks

## Whitebox Overall System

## Motivation

archledger is decomposed into focused black-box building blocks within one white-box system. The current Building Block View includes CLI, Config, Repository, Render, Storage, Model, Assembly, Dialect, Section Rendering, Converter, Source Tracking, Migration, Record Type Registry, Check, Source Ref Validation, ID Utilities, Renumber Service, and ID Segment Resolution.

## Contained building blocks

- **CLI Layer** (`cli.py`, `cli_formatting.py`, `cli_payloads.py`, `launcher.py`): Typer-based command-line interface with 14 top-level commands plus the `source` subgroup (`snapshot`, `changed`, `convert`), JSON payload construction, and human-readable output formatting
- **Config Layer** (`config/`): Project configuration model, TOML parsing, default config rendering
- **Repository Layer** (`repository.py`): Business logic orchestration for init, create, list/show/read, check, archive, doctor, and status workflows
- **Model Layer** (`model.py`, `errors.py`): Core data structures, validation constants, record lifecycle
- **Record Type Registry** (`record_types.py`): Record type specifications, directory/template/section mappings, CLI kind aliases
- **Check Layer** (`checks.py`): Per-record-type content validation including multi-type diagram validation (text/ascii/unicode/svgbob/mermaid) with dialect-specific block detection and line-length checks
- **Source Ref Validation** (`source_refs.py`): Traceability link normalization and path validation
- **Storage Layer** (`storage/`): File system access, front matter parsing, source state persistence
- **Assembly Layer** (`assembly.py`): Jinja2-based document assembly from records and sections
- **Dialect Layer** (`dialects.py`): Format-neutral markup abstraction (Markdown, AsciiDoc)
- **Section Rendering Layer** (`section_rendering.py`): Per-record-type rendering via dialects
- **Render Layer** (`render.py`): Build pipeline facade
- **Converter Layer** (`converters.py`, `conversion_plan.py`, `formats.py`): Multi-format export planning and execution via pandoc/asciidoctor
- **Source Tracking Layer** (`source_tracking.py`, `storage/source_state.py`): Change detection and impact analysis
- **Migration Layer** (`migration.py`): Source dialect conversion (Markdown to AsciiDoc)
- **ID Utilities** (`ids.py`): ID parsing and formatting helpers for ledger-prefixed IDs
- **Renumber Service** (`renumber.py`): ID migration planning and apply operations across records and links
- **ID Segment Resolution** (`id_segments.py`): Segment-aware ID routing and section scoping logic

## Important interfaces

The primary interface is the CLI (`archledger` console script). The CLI delegates to `cli_payloads.py` for JSON output construction and `cli_formatting.py` for human-readable messages. Internally, the Repository exposes methods that the CLI calls, and the Repository delegates to Storage, Model, Record Type Registry, Check, and Source Ref Validation. Config parsing is handled by the Config Layer independently from Storage. The Render Layer delegates to Assembly and Converters. The Converter Layer uses `conversion_plan.py` to plan each format conversion. Source Tracking is used by the CLI `source` subgroup for snapshot/changed/convert commands.

### Level 1

#### CLI Layer

**Parent:** al_block_0041
**Interfaces:** archledger console script (stdin/stdout)
**Location:** archledger/cli.py, archledger/cli_formatting.py, archledger/cli_payloads.py, archledger/launcher.py

The Typer-based CLI exposes top-level commands: `init`, `status`, `paths`, `schema`, `new`, `seed`, `list`, `show`, `read`, `check`, `archive`, `doctor`, `renumber`, `build`, and the `source` subgroup. The `source` subgroup contains `snapshot`, `changed`, and `convert` for source tracking and dialect migration. `archive` preserves obsolete records without reusing ledger numbers, and `doctor` validates or repairs ledger numbering invariants. Each command resolves the project config, constructs a Repository, and delegates to it. Two output modes are supported: human-readable text (default) and structured JSON (`--json` flag). Error handling maps domain exceptions (`ArchledgerError` subclasses) to appropriate exit codes and error output.

Output is split across three modules: `cli.py` defines Typer commands and dispatches to the Repository, `cli_payloads.py` constructs structured JSON dictionaries from domain result types, and `cli_formatting.py` renders human-readable messages from those payloads. This separation keeps the command definitions thin and testable.

The `init` command accepts comprehensive CLI options covering all configuration domains: build defaults (`--build-default-format`, `--build-converter`, `--build-pdf-engine`, etc.), diagrams (`--diagrams`, `--diagram-renderer`, `--diagram-default-type`), arc42 metadata (`--arc42-title`, `--arc42-language`, `--arc42-template-version`), source tracking (`--tracking/--no-tracking`, `--tracking-scanner`, `--tracking-include`, `--tracking-exclude`), and ID format (`--id-prefix`, `--id-width`, `--id-segment-mode`). Options are validated against shared constants from `config/model.py` before config generation.

The `renumber` command delegates to the Renumber Service (`renumber.py`) to replan and optionally apply ID format changes. It is dry-run by default; `--apply` is required to execute mutations. It accepts `--id-prefix`, `--id-width`, and `--id-segment-mode` to specify the target format.

The `source snapshot` and `source changed` commands integrate the source tracking subsystem. The `source convert` command delegates to the migration module for Markdown-to-AsciiDoc source conversion.

#### Repository Layer

**Parent:** al_block_0041
**Interfaces:** create_record(), list_records(), get_record(), load_all_records(), check(), init(), status()
**Location:** archledger/repository.py

The `ArchitectureRepository` class is the central business logic layer. It orchestrates record creation (allocating IDs via the Record Type Registry using the configured `LedgerIdFormat` and segment resolution from `id_segments.py`, rendering templates, writing files), record loading (parsing front matter, validating fields including ID syntax and segment expectations, normalizing source refs via the Source Ref Validation layer), integrity checks (delegating per-record-type content warnings to the Check Layer, plus cross-reference validation and source contract validation), and initialization (directory scaffolding, section file generation with init-time ID format options). It holds a Jinja2 environment for template rendering.

Record ID allocation uses `ProjectConfig.id_format` to format the next number with the configured prefix, width, and segment. In segmented mode, the segment is resolved via `id_segment_for_new_record()` from the record kind and config `segment_map`.

#### Render Layer

**Parent:** al_block_0041
**Interfaces:** build_document()
**Location:** archledger/render.py

The render module (`render.py`) is a thin facade that orchestrates the build pipeline. It resolves requested output formats via the formats module, delegates document assembly to the Assembly Layer, and then delegates multi-format conversion to the Converter Layer. The actual rendering logic is split across the Assembly Layer (template orchestration) and the Section Rendering Layer (per-record-type output).

#### Storage Layer

**Parent:** al_block_0041
**Interfaces:** read_text() / write_text(), read_markdown_front_matter(), resolve_project_paths(), read_source_state() / write_source_state()
**Location:** archledger/storage/common.py, archledger/storage/frontmatter.py, archledger/storage/meta.py, archledger/storage/paths.py, archledger/storage/source_state.py

The storage subpackage handles all file system I/O. `paths.py` discovers the project config and resolves directory layout (including `source_state_path` for tracking baselines). `project_config.py` holds the `ProjectConfig` dataclass with all configuration fields (source, build, arc42, skill, tracking). Config parsing and TOML loading now lives in the Config Layer (`config/` subpackage). `frontmatter.py` parses Markdown/AsciiDoc files with YAML front matter into metadata dict and body string, and provides `iter_source_files` for directory enumeration. `meta.py` manages the storage metadata file (`storage.yaml`). `source_state.py` reads and writes source tracking state as JSON. `common.py` provides `write_text`, `read_text`, `ensure_dir`, and `utc_now_iso`.

#### Model Layer

**Parent:** al_block_0041
**Interfaces:** ArchitectureRecord dataclass, SourceRef dataclass, validate_record(), filename_for(), record_sort_key(), normalize_kind()
**Location:** archledger/model.py, archledger/errors.py

The model module defines the core data structures and validation rules. `ArchitectureRecord` is a frozen dataclass holding id, type, title, status, section, order, path, metadata, body, and source_refs. `SourceRef` holds path, symbols, and reason for traceability linking. `validate_record()` checks field types, status values, and ID/filename consistency. Constants for valid formats, status values, and file extension mappings remain in `model.py`. Record type to directory/template/section mappings have been extracted to the Record Type Registry (`record_types.py`). Source ref validation and normalization have been extracted to the Source Ref Validation layer (`source_refs.py`). The `errors.py` module defines the exception hierarchy: `ArchledgerError` base with `ConfigError`, `StorageError`, `FrontMatterError`, `ValidationError`, and `RenderError` subclasses.

#### Assembly Layer

**Parent:** al_block_0041
**Interfaces:** assemble_document(), assemble_asciidoc_document()
**Location:** archledger/assembly.py

The assembly module loads all records from the repository, groups them by arc42 section, filters by visibility, selects the correct dialect, and renders a single document using a Jinja2 template (`arc42_document.md.j2` or `arc42_document.adoc.j2`). It delegates to the Section Rendering Layer for per-record-type output formatting. The assembly runs a check first and blocks the build if errors are found.

#### Dialect Layer

**Parent:** al_block_0041
**Interfaces:** get_dialect(), Dialect base class, MarkdownDialect / AsciiDocDialect
**Location:** archledger/dialects.py

The dialects module provides a format-neutral abstraction for document rendering. The `Dialect` base class defines methods for headings, tables, bullets, and strong text. `MarkdownDialect` and `AsciiDocDialect` implement these using the respective markup conventions (e.g., `#` vs `=` for headings, `|...|` vs `|===` tables). Both the Assembly Layer and Section Rendering Layer use dialects to produce format-correct output without conditional branching.

#### Section Rendering Layer

**Parent:** al_block_0041
**Interfaces:** section_body(), building_block_hierarchy(), adr_sections(), quality_scenarios(), risk_table(), glossary_table(), (and other per-type renderers)
**Location:** archledger/section_rendering.py

The section rendering module contains all per-record-type rendering functions. Each function takes a list of `ArchitectureRecord` and a `Dialect`, and returns a format-appropriate string (Markdown or AsciiDoc). Functions include table renderers (quality goals, stakeholders, quality scenarios, risks, glossary), list renderers (constraints, context interfaces), hierarchy renderers (building blocks with white/black boxes and interfaces), and prose renderers (ADRs, runtime scenarios, deployment, concepts, strategy items).

#### Converter Layer

**Parent:** al_block_0041
**Interfaces:** convert_assembled_document()
**Location:** archledger/converters.py, archledger/conversion_plan.py, archledger/formats.py

The converter module handles multi-format export. It takes an assembled document (from the Assembly Layer) and produces output in the requested formats. For native format builds (Markdown source to Markdown output, or AsciiDoc source to AsciiDoc output), it does a direct file copy. For other formats, it invokes external converters: pandoc for Markdown-to-HTML/PDF/DOCX/RST/Textile, asciidoctor for AsciiDoc-to-HTML/PDF (direct or via DocBook intermediate), and pandoc for AsciiDoc-to-DOCX/Markdown/RST/Textile (via DocBook). The formats module (`formats.py`) defines the `OutputFormat` enum and resolves requested formats from CLI options and config.

Conversion planning is handled by `conversion_plan.py`, which produces a `ConversionPlan` dataclass for each requested format. Each plan specifies whether the conversion is a native copy, a direct tool invocation, or requires a DocBook intermediate step. Tool resolution uses `shutil.which` by default. The `require_tool()` function raises `RenderError` with install hints when a required converter is unavailable. DocBook intermediates are cleaned up unless `build_keep_intermediate` is set.

#### Source Tracking Layer

**Parent:** al_block_0041
**Interfaces:** scan_workspace(), diff_source_states(), resolve_impacts()
**Location:** archledger/source_tracking.py, archledger/storage/source_state.py

The source tracking module detects changes between a baseline snapshot and the current workspace state. `scan_workspace` enumerates tracked files using git or filesystem scanning, computes SHA-256 content hashes, and stores SHA-256-only file entries. It also derives directory hashes and file counts from the scanned file tree. `diff_source_states` compares two snapshots to produce a `ChangeSet` listing added, modified, and deleted files with possible rename detection. `resolve_impacts` cross-references changed files with architecture record `source_refs` to identify impacted records and unlinked changed files.

The storage sub-module (`storage/source_state.py`) handles JSON serialization and deserialization of the source state, persisted alongside `storage.yaml`.

#### Migration Layer

**Parent:** al_block_0041
**Interfaces:** convert_sources()
**Location:** archledger/migration.py

The migration module converts source fragments from one dialect to another. Currently supports Markdown-to-AsciiDoc conversion. It iterates over all section and record files, converts the body using pandoc (falling back to keeping the original body if pandoc is unavailable), updates the YAML front matter to reflect the new body format, and optionally replaces the original files. It also rewrites the project config to target the new source format. Migration was updated to handle configurable ID format fields during config rewriting.

#### Config Layer

**Parent:** al_block_0041
**Interfaces:** load_project_config(), build_default_project_config(), render_project_config(), ProjectConfig dataclass
**Location:** archledger/config/**init**.py, archledger/config/model.py, archledger/config/parse.py, archledger/config/render.py

The `config` subpackage owns all project configuration concerns. `config/model.py` defines frozen dataclasses for each configuration domain: `SourceConfig`, `BuildConfig` (with nested `BuildOutputConfig`), `Arc42Config`, `SkillConfig`, `TrackingConfig`, and the unified `ProjectConfig` facade that composes them via properties. It also exports public allowed-value constants (`VALID_BUILD_CONVERTERS`, `VALID_DIAGRAM_RENDERERS`, `VALID_DIAGRAM_TYPES`, `VALID_DIAGRAM_IMAGE_FORMATS`, `VALID_TRACKING_SCANNERS`) shared by `parse.py`, `render.py`, and `cli.py`.

`ProjectConfig` includes ID format fields: `id_prefix` (default `al`), `id_width` (default `4`), `id_segment_mode` (default `none`), `id_default_segment`, and `id_segment_map`. The `id_format` property constructs a `LedgerIdFormat` instance from these fields, providing the canonical ID formatting object used throughout the repository, check, and renumber layers.

`config/parse.py` loads and validates `archledger.toml` using `tomllib` (or `tomli` for Python < 3.11), with strict key validation and environment variable expansion. It parses the `[ids]` section, validating prefix, width, segment mode, and segment map using validators from `ids.py`. `config/render.py` generates default configuration files for `archledger init` via a two-stage pipeline: `build_default_project_config()` constructs a validated `ProjectConfig` dataclass from init parameters (including build, diagram, arc42, tracking, and ID format options), and `render_project_config()` serializes it to TOML.

The `[diagrams]` section supports five diagram types (`text`, `ascii`, `unicode`, `svgbob`, `mermaid`) and three renderers (`pass-through`, `mermaid-cli`, `asciidoctor-diagram`). The default diagram type is `text`, ensuring that new diagram records produce readable text-based diagrams in native builds without any external tooling.

The `[ids]` section (config version 7+) configures the ledger ID format: `prefix`, `width`, `segment_mode`, `default_segment`, and `segment_map`. Projects created without this section fall back to `al` prefix, width 4, and `none` segment mode, preserving backward compatibility.

#### Record Type Registry

**Parent:** al_block_0041
**Interfaces:** RECORD_TYPES registry, CLI_KIND_ALIASES, RecordTypeSpec dataclass
**Location:** archledger/record_types.py

The `record_types.py` module is the central registry for all arc42 record types. It defines `RecordTypeSpec`, a frozen dataclass mapping each record kind to its directory name, filename prefix, default section, template basename, CLI aliases, default status/level, and a context factory function. The `RECORD_TYPES` dictionary provides the authoritative lookup. `CLI_KIND_ALIASES` maps alternative names (e.g., `qg` for `quality_goal`) for the CLI.

The diagram context factory defaults `diagram_type` to `"text"` (previously `"mermaid"`). Supported diagram types are `text`, `ascii`, `unicode`, `svgbob`, and `mermaid`. The default can be overridden per-project via the `[diagrams].default_type` config key, which the Repository Layer passes through when creating diagram records.

This module was extracted from `model.py` to keep the model focused on data structures while record type configuration lives in one discoverable location.

#### Check Layer

**Parent:** al_block_0041
**Interfaces:** content_warnings()
**Location:** archledger/checks.py

The `checks.py` module provides per-record-type content validation beyond structural checks. The main entry point is `content_warnings()`, which returns a list of warning strings for a given `ArchitectureRecord`. It dispatches to type-specific checkers registered in `_CONTENT_WARNING_CHECKERS`: quality goals require scenarios, stakeholders require expectations, constraints require impact and valid categories, ADRs require Context/Decision/Consequences sections and deciders, quality scenarios require measurable response measures, risks require valid severity/probability and mitigation, and so on. It also detects placeholder text in record bodies and cross-dialect syntax contamination (e.g., AsciiDoc headings in Markdown records).

For diagram records, the check layer validates the `diagram_type` field against the allowed set (`text`, `ascii`, `unicode`, `svgbob`, `mermaid`), verifies that the body contains the appropriate fenced or literal block for the declared type and source dialect (Markdown uses ` ```textdiagram `/` ```svgbob `/` ```mermaid ` fences; AsciiDoc uses `[source,text]`+`----`, `[svgbob]`+`....`, or `[mermaid]`+`....` blocks), and checks for empty diagram blocks. Text-type diagrams (`text`, `ascii`, `unicode`) receive an additional line-length check (120 characters max) to keep diagrams readable in terminals and Git diffs.

This module was extracted from `repository.py` to isolate validation logic.

#### Source Ref Validation

**Parent:** al_block_0041
**Interfaces:** normalize_source_refs(), validate_relative_posix_path()
**Location:** archledger/source_refs.py

The `source_refs.py` module handles validation and normalization of source traceability links on architecture records. `validate_relative_posix_path()` enforces that source ref paths are relative, use POSIX separators, and do not traverse parent directories. `normalize_source_refs()` processes the raw `source_refs` list from YAML front matter, supporting both shorthand string syntax (`path/to/file.py#SymbolName`) and full mapping syntax with explicit path, symbols, and reason. It verifies that referenced paths and directories actually exist in the workspace. `RelativePosixPathError` provides structured error reporting for invalid paths. This module was extracted from `model.py` to keep source ref validation independent from the core data model.

#### ID Utilities

**Parent:** al_block_0041
**Interfaces:** LedgerIdFormat.format(), LedgerIdFormat.parse(), LedgerIdFormat.parse_parts(), LedgerIdFormat.is_id(), LedgerIdFormat.pattern(), LedgerIdFormat.reference_pattern(), format_ledger_id(), parse_ledger_id(), parse_ledger_id_parts(), is_ledger_id(), filename_for_ledger_id(), ledger_id_from_filename(), validate_id_prefix(), validate_id_width(), validate_id_segment_mode(), validate_id_segment()
**Location:** archledger/ids.py

The `ids` module provides centralized ledger ID handling with configurable prefix, width, and segment mode. The core abstraction is `LedgerIdFormat`, a frozen dataclass that encapsulates the three ID format parameters and exposes methods for formatting, parsing, pattern generation, and validation.

**Unsegmented mode** (`segment_mode=none`, default): IDs follow `<prefix>_<number>` (e.g., `al_0001`). `format(number)` produces the zero-padded string, `parse(id)` extracts the number, and `pattern()`/`reference_pattern()` produce regexes for exact matching and cross-reference detection respectively.

**Segmented mode** (`segment_mode=type`): IDs follow `<prefix>_<segment>_<number>` (e.g., `al_adr_0077`). `format(number, segment=...)` includes the validated segment token, and `parse_parts()` returns a `ParsedLedgerId` with both `number` and `segment` fields.

Module-level convenience functions (`format_ledger_id`, `parse_ledger_id`, `is_ledger_id`, etc.) accept optional `prefix`, `width`, and `segment_mode` parameters for callers that need ad-hoc format handling. Validators (`validate_id_prefix`, `validate_id_width`, `validate_id_segment_mode`, `validate_id_segment`) enforce format constraints shared across config parsing, CLI validation, and record checks.

The `LedgerIdFormat` instance is constructed from `ProjectConfig.id_format` and threaded through repository, renumber, and check operations as the single source of truth for ID syntax rules.

#### Renumber Service

**Parent:** al_block_0041
**Interfaces:** renumber_project()
**Location:** archledger/renumber.py

The `renumber` module provides the `renumber_project()` service that replans and optionally applies changes to the ledger ID format across all source files. It supports changing the ID prefix, width, and segment mode.

The renumber workflow operates in two phases: first it builds a rename plan (collecting numbered paths, computing new IDs via the configured `LedgerIdFormat` and segment resolution) and a rewrite plan (finding and replacing all ID references in source files). Then, if `apply=True`, it atomically rewrites file contents, renames files via a two-phase temp-file strategy to avoid collisions, updates `archledger.toml` with the new ID format settings, and recomputes `storage.yaml` counters.

When `apply=False` (dry-run, the default), it validates the plan and returns the computed changes without modifying any files. The CLI `renumber` command delegates to this service and formats the result for human or JSON output.

Key data structures: `RenumberResult` (top-level result with old/new format, renamed paths, rewritten files), `RenumberedPath` (old/new ID and path pair), and `RewrittenFile` (path with replacement count).

#### ID Segment Resolution

**Parent:** al_block_0041
**Interfaces:** id_segment_for_metadata(), id_segment_for_record(), id_segment_for_new_record()
**Location:** archledger/id_segments.py

The `id_segments` module resolves content-derived ID segments for segmented ledger IDs. When `segment_mode` is `type`, each record ID includes a segment token derived from the record's type metadata.

Resolution priority:

1. Explicit `id_segment` in the record's front matter metadata.
2. Mapped segment from the configured `segment_map` keyed by record `type`.
3. The configured `default_segment` as fallback.

Three entry points serve different callers: `id_segment_for_metadata()` for raw metadata dicts (used by renumber), `id_segment_for_record()` for loaded `ArchitectureRecord` objects (used by repository), and `id_segment_for_new_record()` for record creation where the kind is known but no record exists yet. All three validate the resolved segment against the `ID_SEGMENT_PATTERN` regex via `validate_id_segment()`.

This module is intentionally thin — it isolates the resolution policy so that `renumber.py` and `repository.py` share the same logic without coupling to each other.

## Interfaces

### CLI stdout JSON contract

**Providers:** CLI Layer
**Consumers:** Automation scripts, JSON-mode CLI users
**Protocol:** JSON over stdout
This interface defines the stable stdout contract for CLI commands when users opt into `--json` mode.

- **Provider**: CLI Layer (`archledger/cli.py`) with payload shaping in `archledger/cli_payloads.py`.
- **Consumers**: automation scripts, coding-agent loops, CI checks, and tests that parse JSON output.
- **Protocol**: JSON object payloads emitted to stdout on success and JSON error payloads on handled failures.

The contract guarantees machine-readable top-level fields (`ok`, `command`, and command-specific result payloads) so tooling can branch on command outcomes without scraping human text output.

### Front matter record file contract

**Providers:** Storage layer, Repository layer
**Consumers:** Check/read/build pipelines, Migration flows
**Protocol:** YAML front matter + Markdown/AsciiDoc body
This interface defines the record-file contract used by source fragments under `.archledger/records/`.

- **Provider**: storage/front matter parser/writer and repository record creation flows.
- **Consumers**: check/read/build pipelines, migration flows, and tooling that edits architecture records directly.
- **Protocol**: record files contain YAML front matter plus a body in the configured dialect (`body_format`) with required metadata fields validated by schema and checks.

The contract preserves deterministic parsing, explicit status/lifecycle metadata, and compatibility with source-schema v2 validation.

# Runtime View

Key runtime scenarios: initializing a new project (scaffolding directories and section files), creating and rendering records (the primary authoring flow), validating records with check (ensuring consistency and completeness), building multi-format output (assembly plus optional conversion), taking source snapshots and detecting changes (source tracking), and converting source dialects (Markdown to AsciiDoc migration).

See the [Build Pipeline Flow diagram](#diagram-al_diagram_0059) for a visual overview of the four-stage pipeline.

## Build Pipeline Flow

The build pipeline processes architecture records through four stages. Native
Markdown and AsciiDoc builds require no external tools. Non-native exports
delegate to pandoc or asciidoctor.

```textdiagram
┌──────────┐      ┌───────────┐      ┌────────────┐      ┌──────────┐
│  Author  │─────>│ Validate  │─────>│  Assemble  │─────>│  Export  │
├──────────┤      ├───────────┤      ├────────────┤      ├──────────┤
│          │      │ Parse     │      │ Load recs  │      │ Plan     │
│ Create / │      │ front     │      │ & sections │      │ conver-  │
│ edit     │      │ matter    │      │            │      │ sion     │
│ record   │      │           │      │ Resolve    │      │          │
│ files    │      │ Check     │      │ dialect    │      │ Native?  │
│          │      │ schema +  │      │            │      │  yes:    │
│          │      │ cross-    │      │ Render     │      │   copy   │
│          │      │ refs      │      │ Jinja2     │      │  no:     │
│          │      │           │      │ template   │      │   pandoc │
│          │      │ Type-     │      │            │      │   or     │
│          │      │ specific  │      │ Write      │      │   asc-   │
│          │      │ checks    │      │ native doc │      │   iido-  │
│          │      │           │      │            │      │   ctor   │
└──────────┘      └───────────┘      └────────────┘      └──────────┘
    new              check             build              build
                                      --format            --format
```

**Caption:** The four-stage pipeline from authoring to export

## Create and render a new architecture record

1. CLI parses the `new` command arguments (kind, title, status, parent, section).
2. CLI resolves the project config via Storage paths.
3. CLI constructs an ArchitectureRepository instance.
4. Repository normalizes the kind alias to a canonical record type.
5. Repository recomputes next-number counters from existing files.
6. Repository renders a Jinja2 template with the new record's context.
7. Repository writes the rendered Markdown file to the appropriate records subdirectory.
8. Repository updates the storage metadata counters.
9. User then invokes `archledger build` to reassemble the full document.
10. Render layer loads all records, sorts by section and order, and produces the final Markdown.

## Validate records with check

1. CLI resolves the project config.
2. Repository iterates over all Markdown files in sections/ and records/.
3. For each file, Storage parses front matter. Repository validates required fields, types, and ID/filename consistency.
4. Repository checks cross-references: parent IDs must exist, duplicate IDs are flagged.
5. Repository detects placeholder text in record bodies.
6. Repository emits type-specific warnings (ADR without deciders, risk without mitigation, glossary without definition, etc.).
7. If `--strict`, warnings are treated as errors.
8. Results are emitted as JSON or human-readable summary.

## Initialize a new project

1. CLI checks that `archledger.toml` does not already exist.
2. CLI collects init options for all configuration domains: build defaults (`--build-default-format`, `--build-default-output`, `--build-converter`, etc.), diagrams (`--diagrams`, `--diagram-renderer`, `--diagram-default-type`), arc42 metadata (`--arc42-title`, `--arc42-language`, `--arc42-template-version`), source tracking (`--tracking/--no-tracking`, `--tracking-scanner`, `--tracking-include`, `--tracking-exclude`), and ID format (`--id-prefix`, `--id-width`, `--id-segment-mode`). Each option maps directly to a field in `archledger.toml`.
3. CLI calls `build_default_project_config()` to construct a validated `ProjectConfig` dataclass, then renders it to TOML via `render_project_config()`.
4. CLI writes the config file and resolves project paths.
5. Repository creates the archledger_dir, sections_dir, records_dir, and build_dir.
6. Repository creates one subdirectory for each unique record type directory from `RECORD_TYPE_TO_DIR` (currently 16 directories).
7. Repository writes 12 section files named with the configured ledger ID format and section extension, for example `al_0001.adoc` in unsegmented AsciiDoc projects or `al_content_0001.md` in segmented Markdown projects.
8. Repository writes the storage.yaml metadata file.
9. The project is ready for `archledger new` commands. Record creation will use the configured ID format (prefix, width, segment mode).

## Build multi-format output

1. CLI resolves the project config and constructs a Repository.
2. Render layer resolves requested output formats from CLI options and config defaults via the formats module.
3. Assembly layer runs check to validate records, then loads all visible records, selects the dialect matching the source format, and renders the document using the appropriate Jinja2 template.
4. Assembly layer writes the native-format assembled document to the build directory.
5. Converter layer computes a conversion plan for each requested non-native format.
6. For native format: file copy. For pandoc-based: invoke pandoc with the appropriate input/output format. For asciidoctor-based: invoke asciidoctor or asciidoctor-pdf directly, or via DocBook intermediate.
7. Results are reported as JSON or human-readable output.

## Detect changed files and impacted records

1. CLI loads the tracking baseline from the source state JSON file (if it exists).
2. Source tracking scans the current workspace, computing SHA-256 hashes for all tracked files.
3. Source tracking diffs the baseline against the current state to produce a ChangeSet (added, modified, deleted files, possible renames).
4. Repository loads all architecture records (including sections).
5. Source tracking resolves impacts by matching changed file paths against record `source_refs`.
6. Results include: impacted records (with matched refs), impacted sections, and unlinked changed files.
7. If no baseline exists, all files are reported as unbaselined.

## Renumber ledger IDs

1. User invokes `archledger renumber --id-prefix <new>` and/or `--id-width <n>` and/or `--id-segment-mode <mode>`.
2. CLI validates options and delegates to `renumber_project()` in `renumber.py`.
3. The renumber service collects all numbered source files from sections, records, and archive directories, parsing each with the current `LedgerIdFormat`.
4. For each file, it computes the new ID using the new format and segment resolution from `id_segments.py`.
5. It builds a rename plan and a rewrite plan (finding all ID references across all source files).
6. It validates no duplicate source IDs and no target collisions.
7. Without `--apply`: returns the plan as JSON or formatted text and exits.
8. With `--apply`: rewrites file contents, renames files via two-phase temp strategy, updates `archledger.toml`, and recomputes `storage.yaml`.
9. CLI outputs the summary of renamed files and rewritten references.

# Deployment View

archledger runs as a local CLI tool on developer machines and in CI runners. There is no server component. The storage directory can be co-located with the source repository or placed in an external path via configuration.

See the [Deployment Topology diagram](#diagram-al_diagram_0063) for a visual overview of deployment nodes.

## Deployment Topology

archledger has no server component. It runs as a local CLI tool on developer
machines and in CI runners. The storage directory is co-located with the source
repository.

```textdiagram
┌─ Developer Machine ───────────────────────────────────────────┐
│                                                               │
│  Python 3.10+ (venv / system)                                 │
│       │                                                       │
│  ┌────▼───────────┐   ┌──────────────┐  ┌──────────────────┐ │
│  │ archledger CLI │──>│  Workspace   │  │  Build Output    │ │
│  │ (console       │   │ .archledger/ │  │ ARCHITECTURE.md  │ │
│  │  script)       │   │  + source/   │  │  + exports       │ │
│  └────────────────┘   └──────────────┘  └──────────────────┘ │
│       │ optional                                              │
│  ┌────▼────────────────┐                                     │
│  │ pandoc / asciidoctor│                                     │
│  └─────────────────────┘                                     │
└───────────────────────────────────────────────────────────────┘

┌─ CI Runner ──────────────────────────────────────────────────┐
│  Python 3.10+ ──> archledger CLI ──> Build Artifacts        │
└────────────────────────────────┬─────────────────────────────┘
                                 │ publish
                                 ▼
                          ┌──────────────┐
                          │ Docs Hosting │
                          └──────────────┘

┌─ PyPI ──────────────┐
│ archledger wheel    │── pip install ──> Developer Machine
│                     │── pip install ──> CI Runner
└─────────────────────┘
```

**Caption:** archledger deployment nodes and their relationships

## Local development

Developer machine with Python >= 3.10. archledger is installed via `pip install -e .` in a virtual environment. The project directory contains `archledger.toml` at the root. The storage directory (default `.archledger/`) holds sections, records, and build output. No network access, database, or server process is required.

## CI pipeline

CI runners execute `archledger check` to validate record integrity and `archledger build --output docs/architecture.md` to produce the rendered document. The built Markdown file is published as a CI artifact. Non-zero exit codes from `check` fail the pipeline.

## PyPI and wheel installation

Distribution targets are PyPI source/wheel artifacts built from this repository. Release pipelines build wheel/sdist and publish versioned packages for installation with `pip install archledger`.

## Console script entry point

The runtime entry point is the console script `archledger = "archledger.launcher:main"`, installed via package metadata and executed in local/CI environments.

## Optional converter toolchain

Optional conversion toolchain: pandoc (html/docx/rst/textile), asciidoctor (html), and asciidoctor-pdf (pdf). Native source-format builds do not require these tools.

## Documentation publishing

Documentation publishing includes README guidance, Sphinx docs in `docs/`, and generated `ARCHITECTURE.md` produced from `.archledger` sources.

## CI release validation

CI release validation runs unit tests, package build checks, version consistency checks, and release workflow documentation checks before publishing.

# Cross-cutting Concepts

Four cross-cutting concepts pervade the architecture: the record lifecycle (draft, proposed, accepted, deprecated, superseded) which controls visibility and validation behavior, the config discovery mechanism which resolves project paths from the workspace directory upward, the dialect abstraction which ensures format-neutral rendering for both Markdown and AsciiDoc sources, and the multi-type diagram record system which supports text, ascii, unicode, svgbob, and mermaid diagram types with type-appropriate validation and templating.

A fourth cross-cutting concern is source tracking and change impact analysis, which is visualized in the [Source Tracking Flow diagram](#diagram-al_diagram_0076).

## Source Tracking Flow

Source tracking compares a saved baseline against the current workspace state. It uses SHA-256 file hashes and matches changed paths against record `source_refs` to report impacted architecture records.

```mermaid
sequenceDiagram
    participant User
    participant CLI as archledger CLI
    participant Tracking as Source Tracking
    participant Storage as Storage Layer
    participant Records as Architecture Records

    User->>CLI: archledger source snapshot
    CLI->>Storage: scan workspace files
    Storage-->>Tracking: file list + SHA-256 hashes
    Tracking->>Storage: persist source-state.json
    Tracking-->>CLI: snapshot confirmed

    Note over User,Records: Later, after code changes...

    User->>CLI: archledger source changed
    CLI->>Storage: load source-state.json
    Storage-->>Tracking: baseline hashes
    CLI->>Storage: scan workspace files
    Storage-->>Tracking: current hashes
    Tracking->>Tracking: diff baseline vs current
    Note right of Tracking: added / modified / deleted\npossible renames
    CLI->>Records: load all records with source_refs
    Records-->>Tracking: source_refs per record
    Tracking->>Tracking: match changed paths to refs
    Note right of Tracking: impacted records\nimpacted sections\nunlinked changed files
    Tracking-->>CLI: ChangeSet + impacts
    CLI-->>User: JSON report

    style CLI fill:#4a9eff,color:#fff
    style Tracking fill:#6c5ce7,color:#fff
    style Storage fill:#dfe6e9
    style Records fill:#00b894,color:#fff
```

**Caption:** How source tracking detects changes and maps them to impacted records

## Record lifecycle and status

Every record has a status field that controls its lifecycle: `draft` (incomplete, excluded from default builds), `proposed` (visible but not formally confirmed), `accepted` (confirmed, included by default), `deprecated` (visible but no longer preferred), and `superseded` (hidden unless explicitly included). The `check` command warns about draft records and empty sections. The `build` command only includes records with visible statuses by default; `--include-draft` and `--include-superseded` flags override this.

## Config discovery and path resolution

archledger discovers its project configuration by walking up from the current directory looking for `archledger.toml` or `.archledger.toml`. The `archledger_dir` setting in the config can be relative (resolved from the config file's directory) or absolute (used as-is). This allows the storage directory to live outside the source tree, for example in a separate state repository.

Config parsing is handled by the Config Layer (`config/` subpackage): `config/parse.py` loads and validates the TOML file, `config/model.py` defines typed dataclasses for each configuration domain (source, build, arc42, skill, tracking, ids) and exports shared validation constants, and `config/render.py` generates configuration files via `build_default_project_config()` + `render_project_config()`. Path resolution happens in `storage/paths.py`. The `[ids]` section (config v7+) configures ledger ID prefix, width, segment mode, default segment, and segment map.

## Dialect abstraction for dual-source support

archledger supports both Markdown and AsciiDoc as first-class source formats. The dialect abstraction (`dialects.py`) defines a `Dialect` base class with methods for headings, tables, bullets, and strong text. `MarkdownDialect` and `AsciiDocDialect` implement these using their respective markup conventions. All rendering code in the Section Rendering Layer and Assembly Layer uses dialects rather than hardcoded markup, ensuring that a single rendering codebase produces correct output for both source formats. Templates exist in both `.md.j2` and `.adoc.j2` variants.

For diagram records, the dialect determines the block syntax used in both templates and validation: Markdown diagrams use fenced code blocks (` ```textdiagram `, ` ```svgbob `, ` ```mermaid `), while AsciiDoc diagrams use literal or source blocks (`[source,text]`+`----`, `[svgbob]`+`....`, `[mermaid]`+`....`). Text-based diagram types (`text`, `ascii`, `unicode`) use the same fenced/literal block syntax within each dialect, differing only in the content characters used.

## Source tracking and change impact analysis

The source tracking subsystem allows agents to detect which workspace files changed since the last baseline snapshot and which architecture records are impacted. A snapshot (`archledger source snapshot`) records SHA-256 hashes of all tracked files. The `source changed` command computes the diff between the baseline and current state, then cross-references changed files with record `source_refs` to identify impacted records and sections. Files that changed but have no linked records are reported as unlinked. This enables agents to update only the documentation affected by code changes.

## Multi-type diagram records

Diagram records support five types: `text`, `ascii`, `unicode`, `svgbob`, and `mermaid`. The default type is `text`, configured via `[diagrams].default_type` in `archledger.toml` and overridable per-record with `--diagram-type` on the CLI.

Text-based types (`text`, `ascii`, `unicode`) store diagram content as plain text in fenced Markdown blocks (` ```textdiagram `) or AsciiDoc literal blocks (`[source,text]` + `----`). They render directly in native builds without external tools, are readable in Git diffs and terminals, and are validated with a 120-character line-length limit.

`svgbob` uses the svgbob markup syntax in dedicated fenced/literal blocks. `mermaid` uses Mermaid syntax in dedicated fenced/literal blocks and requires an external renderer (`mermaid-cli` or `asciidoctor-diagram`) for image output. Three diagram renderers are supported: `pass-through` (default, embeds source as-is), `mermaid-cli`, and `asciidoctor-diagram`.

The Check Layer validates diagram type against the allowed set, verifies that the body contains the correct block syntax for the declared type and dialect, checks for empty blocks, and enforces line-length limits on text diagrams. Templates produce type-appropriate scaffolding when creating new diagram records.

## Configurable ledger ID format

## Concept

Ledger IDs identify architecture records throughout the system. The ID format is configurable per project via the `[ids]` section in `archledger.toml`, but the single global numeric sequence is always preserved.

### Unsegmented mode (default)

Format: `<prefix>_<number>` (e.g., `al_0001`). The prefix defaults to `al` and width to 4 digits. IDs like `al_0042` are valid for any record type.

### Segmented mode (`segment_mode=type`)

Format: `<prefix>_<segment>_<number>` (e.g., `al_adr_0077`, `al_block_0042`). The segment is derived from the record's `type` field via the configured `segment_map`, with an explicit `id_segment` override in front matter, falling back to `default_segment`.

### Resolution chain

1. `LedgerIdFormat` in `ids.py` — parses and formats IDs, provides regex patterns for both exact match and cross-reference detection.
2. `id_segments.py` — resolves the segment token for a record, used by repository (record creation) and renumber (migration).
3. `ProjectConfig.id_format` property — exposes the configured `LedgerIdFormat` to all callers.

### Invariants

- Every record has exactly one numeric ID in the global sequence.
- ID numbers are stable across renumber operations (only prefix/width/segment change).
- File names are derived from the full ID string plus the configured source format extension.
- Cross-references in record bodies are rewritten by the renumber service using the `reference_pattern` regex.

# Architecture Decisions

Key architectural decisions: dual-source support (Markdown and AsciiDoc as first-class formats), Markdown/AsciiDoc records with YAML front matter as the storage format, Typer as the CLI framework, Jinja2 for document rendering, and optional external converters for multi-format export. Each decision was driven by the goals of maintainability, traceability, and reproducibility.

## Use Markdown/AsciiDoc records with YAML front matter

**Status:** accepted
**Date:** 2026-05-20
**Deciders:** Holger
**Supersedes:**
**Related:**

## Context

Architecture documentation needs a storage format that is human-editable, version-control friendly, and machine-parseable. Tools like Structurizr use DSL files, while wiki-based approaches use databases or rich text editors. The project needs to support both Markdown and AsciiDoc communities.

## Decision

Store each architecture record as an individual Markdown or AsciiDoc file with YAML front matter. The front matter holds structured metadata (id, type, status, section, order, parent, source_refs, etc.) and the body holds human-readable prose in the configured dialect. A deterministic build process assembles all records into a single document. A dialect abstraction ensures rendering works identically for both formats.

## Consequences

Positive: files are diffable, mergeable, and editable in any text editor. Coders and agents can read and write records without special tooling. YAML front matter is straightforward to parse with PyYAML. Both Markdown and AsciiDoc communities can use their preferred format.

Negative: no referential integrity enforced at write time (only at check time). No schema validation beyond what the check command implements. Large projects may accumulate many files. Dual-format support adds complexity in templates and rendering.

## Alternatives considered

- Single large Markdown file: harder to merge, no per-record granularity.
- JSON or YAML store: less human-friendly for prose editing.
- Database (SQLite): adds a runtime dependency, harder to diff.
- Structurizr DSL: requires Java tooling, not Markdown-first.
- Markdown only: excludes AsciiDoc communities and their tooling ecosystem.

## Typer CLI over argparse or Click

**Status:** accepted
**Date:** 2026-05-20
**Deciders:** Holger
**Supersedes:**
**Related:**

## Context

The CLI needs type-annotated command definitions, automatic help generation, and support for both human-readable and JSON output modes. Python has multiple CLI frameworks with different tradeoffs.

## Decision

Use Typer for the CLI framework. Typer provides type-annotated command definitions with automatic `--help` generation, option parsing from type hints, and a compact declarative style.

## Consequences

Positive: concise command definitions, automatic help text, good editor support for type annotations. Easy to add new commands.

Negative: Typer adds a dependency. Some advanced CLI patterns require working around Typer's abstractions.

## Alternatives considered

- argparse: built-in, but verbose and lacks type-annotated commands.
- Click: mature and flexible, but decorator-heavy and less type-annotated.
- docopt: declarative but less structured for subcommands.

## Jinja2 for document rendering

**Status:** accepted
**Date:** 2026-05-20
**Deciders:** Holger
**Supersedes:**
**Related:**

## Context

The build step must assemble a single Markdown document from multiple section files and record files. The assembly involves conditional rendering, table generation, and section ordering.

## Decision

Use Jinja2 templates for document rendering. The main template (`arc42_document.md.j2`) is filled by callback functions that format each record type (tables for quality goals, lists for constraints, hierarchies for building blocks, etc.). Record-level templates produce individual Markdown files when creating new records.

## Consequences

Positive: Jinja2 is well-known, supports template inheritance and includes, and is already a dependency. Callback-based rendering keeps the template readable.

Negative: complex rendering logic is split between the template and Python helper functions. Template errors only surface at build time.

## Alternatives considered

- String concatenation in Python: harder to maintain, no template/file separation.
- Mako: less common in this space, different syntax.
- Static site generator (MkDocs, Sphinx): heavier dependency, not designed for single-document output.

## Use SHA-256-only source-state file entries plus directory hashes

**Status:** accepted
**Date:** 2026-05-21
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

Source-state tracking needs strong change detection and compact persisted metadata.

## Decision

Persist per-file SHA-256 hashes only, plus derived directory hashes and counts in source state snapshots.

## Consequences

Improves determinism and avoids unstable file-size/mtime dependence; requires content hashing during scan.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Config v7 and source schema v2 are the release baseline

**Status:** accepted
**Date:** 2026-05-21
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

Repository-local architecture sources must use one supported baseline schema to avoid drift between project dogfooding and generated defaults.

## Decision

Use config v7 (with `[ids]` section for configurable prefix, width, and segment mode) and source schema v2 as the release baseline for this project and generated projects.

## Consequences

Strict checks are consistent; migration effort is required for older local records. The `[ids]` section is optional — projects created with config v5/v6 continue to work with default `al` prefix and width 4.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.
- Separate config version for each new field: rejected because it would proliferate minor versions; bundling ID format changes into v7 is cleaner.

## Native builds require no external tools

**Status:** accepted
**Date:** 2026-05-21
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

Core build workflows should be available in clean Python environments without external binaries.

## Decision

Require no external converter tools for native Markdown/AsciiDoc outputs.

## Consequences

Improves portability; non-native formats remain optional.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Non-native exports delegate to pandoc or asciidoctor

**Status:** accepted
**Date:** 2026-05-21
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

Supporting many export formats inside Python would duplicate mature tooling and increase maintenance burden.

## Decision

Delegate non-native conversions to pandoc/asciidoctor family tools.

## Consequences

Clear dependency errors are required when tools are missing.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Output path resolution remains bounded to configured roots

**Status:** accepted
**Date:** 2026-05-21
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

Architecture output generation must not permit accidental writes outside intended roots.

## Decision

Keep output path resolution bounded by configuration/workspace validation rules.

## Consequences

Safer defaults; invalid paths fail early with explicit diagnostics.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Source refs use relative POSIX paths without parent traversal

**Status:** accepted
**Date:** 2026-05-21
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

Source references must safely link docs to code while preventing ambiguous or unsafe paths.

## Decision

Require relative POSIX source_refs that do not traverse parent directories.

## Consequences

Traceability links stay portable and secure; invalid refs are rejected.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Storage counters are metadata and can be recomputed

**Status:** accepted
**Date:** 2026-05-21
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

Stored counters optimize metadata reads but can drift after manual edits or transfers.

## Decision

Treat storage counters as recomputable metadata, not canonical truth.

## Consequences

Repair/recount operations can restore consistency without data loss.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Multi-type diagram support with text as default

**Status:** accepted
**Date:** 2026-05-22
**Deciders:** archledger maintainers
**Supersedes:**
**Related:** al_adr_0082

## Context

The initial diagram support only handled Mermaid syntax. Mermaid requires a renderer (mermaid-cli, browser, or Kroki) to produce visual output, and its source blocks are not directly readable in terminals or plain-text diff views. Architecture diagrams are often structural decompositions that benefit more from being readable at a glance than from being interactive or visually polished.

## Decision

Support five diagram types: `text`, `ascii`, `unicode`, `svgbob`, and `mermaid`. Default to `text` for new diagram records. Text-based diagrams (`text`, `ascii`, `unicode`) use simple fenced/literal blocks that render directly in Markdown and AsciiDoc builds without any external tool. The Check Layer validates each diagram type with dialect-appropriate block detection and enforces a 120-character line-length limit on text diagrams. Templates produce type-appropriate scaffolding.

## Consequences

Text diagrams are immediately readable in source, Git diffs, terminal output, and native builds. Mermaid remains available for sequence/state/flow diagrams where its syntax is more compact. Text diagrams have a line-length limit to prevent unreadable horizontal scrolling. The diagram type is stored in the record metadata and can be overridden per-record via `--diagram-type` on the CLI. Three renderers are supported (`pass-through`, `mermaid-cli`, `asciidoctor-diagram`), down from an earlier broader set; svgbob, goat, and Kroki renderers were removed to reduce external dependency surface.

## Alternatives considered

- Keep Mermaid as sole diagram type: rejected because it prevents readable text-based diagrams that work without a renderer.
- Support only text diagrams: rejected because Mermaid is better suited for certain diagram categories (sequence, state).
- Make `unicode` the default: rejected because `text` has broader terminal and font compatibility.

## Config v7 adds configurable ID prefix, width, and segment mode

**Status:** proposed
**Date:** 2026-05-23
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

Config v5 hardcoded the ID format as `al_` prefix with 4-digit zero-padded numbers. Projects that manage multiple architecture ledgers (e.g., monorepos with independent sub-project docs) need distinct ID prefixes to avoid confusion when records from different projects appear in the same search or review. Some projects also want wider numbers or a different prefix.

Task-0019 (flexible IDs renumbering) introduced configurable prefix and width. Task-0020 (content segment IDs) added segment mode support. The config schema needed to evolve to persist these settings.

## Decision

Config version 7 adds an `[ids]` section with:

- `prefix` (default: `al`) — 2–16 lowercase alphanumeric characters, must start with a letter.
- `width` (default: `4`) — minimum digit count, range 2–12.
- `segment_mode` (default: `none`) — either `none` for unsegmented `al_NNNN` IDs or `type` for segmented `al_<segment>_NNNN` IDs.
- `default_segment` (default: empty) — fallback segment token when `segment_mode=type`.
- `segment_map` (default: empty dict) — maps record types to segment tokens.

The `init` command accepts `--id-prefix`, `--id-width`, and `--id-segment-mode` options to set these at project creation. `LedgerIdFormat` in `ids.py` is the single source of truth for parsing and formatting IDs according to the configured settings.

## Consequences

- Projects can now use distinct ID prefixes and widths. The `renumber` command migrates existing projects.
- Default behavior is unchanged: new projects still get `al_0001`-style IDs.
- Config files with no `[ids]` section fall back to defaults, so existing projects are forward-compatible.
- Bumping config version to 7 signals the new fields; migration layer handles older configs.

## Alternatives considered

- Separate ID format file: rejected because it would add a new file for a small set of fields that belong alongside other project configuration.
- Hardcoded prefix/width only: rejected because it would not support multi-project disambiguation or type-derived segments.

## Renumber command is dry-run by default

**Status:** proposed
**Date:** 2026-05-23
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

Changing ledger ID format (prefix, width, or segment mode) is a destructive operation that touches every source file in the `.archledger/` directory. File renames, reference rewrites, and config mutations cannot be trivially undone. Users need a safe way to preview changes before committing.

## Decision

The `archledger renumber` command is dry-run by default. It computes the full rename and rewrite plan and reports what would change, without modifying any files. The `--apply` flag is required to execute the plan.

When `--apply` is used, the renumber service:

1. Validates the plan (no duplicate source IDs, no target collisions).
2. Rewrites file contents (replacing all ID references).
3. Renames files via a two-phase temp-file strategy to avoid overwriting in-place.
4. Updates `archledger.toml` with the new format settings.
5. Recomputes `storage.yaml` counter.

## Consequences

- Users can safely experiment with `archledger renumber --id-prefix foo` and review the plan.
- The `--apply` flag makes the destructive nature of the operation explicit.
- JSON output includes full details of planned renames and rewrites for programmatic review.

## Alternatives considered

- Apply by default with `--dry-run`: rejected because the safer convention (default no-op) reduces accident risk.
- Interactive confirmation: rejected because the CLI is designed for both human and agent use; a flag is more machine-friendly.

## Segmented IDs embed type-derived tokens in the ID string

**Status:** proposed
**Date:** 2026-05-23
**Deciders:** archledger maintainers
**Supersedes:**
**Related:**

## Context

In projects with many records (50+), flat `al_NNNN` numbering makes it hard to identify a record's type from its ID alone. Scanning `al_0042` gives no hint whether it is an ADR, building block, or runtime scenario. This hurts navigation in large ledgers and in cross-references between records.

## Decision

When `segment_mode=type`, ledger IDs include a type-derived segment token: `<prefix>_<segment>_<number>` (e.g., `al_adr_0077`, `al_block_0042`). The segment is resolved deterministically from the record's `type` metadata via the configured `segment_map`, with an explicit `id_segment` front-matter field as an override, and `default_segment` as fallback.

Segment tokens are validated against `^[a-z][a-z0-9-]{1,31}$`. The default segment map maps each record type to a short token (e.g., `adr` → `adr`, `white_box` → `block`, `runtime_scenario` → `runtime`).

The global numeric sequence is preserved: numbering remains sequential across all types regardless of segment. Renumber can toggle segment mode on or off while keeping numbers stable.

## Consequences

- IDs become self-describing: `al_adr_0077` is clearly an architecture decision.
- File names sort predictably within type directories (e.g., `.archledger/records/decisions/al_adr_0077.md`).
- Cross-references in record bodies update correctly during renumber.
- The `none` segment mode preserves backward compatibility for projects that prefer flat numbering.

## Alternatives considered

- Per-type counters: rejected because it would break the single global sequence invariant and complicate renumbering.
- Opaque hash segments: rejected because they would not be human-readable.

# Quality Requirements

The top quality scenarios address deterministic builds and agent-friendly CLI interaction. These directly support the quality goals of reproducibility, maintainability, and traceability.

## Quality Requirements Overview

| Title                                      | Category      | Measure                                                                         | Scenarios                        |
| ------------------------------------------ | ------------- | ------------------------------------------------------------------------------- | -------------------------------- |
| Deterministic native build output          | reliability   | Byte-identical output for equal accepted records and deterministic date source. | al_quality_0093, al_quality_0101 |
| Fast check and build on small repositories | performance   | check/build complete in under 5s on representative small repositories.          | al_quality_0101                  |
| Safe path validation                       | safety        | Path escape attempts are rejected with explicit errors.                         | al_quality_0099                  |
| Clear converter failure diagnostics        | operability   | Converter failures identify missing tool and installation hint.                 | al_quality_0095                  |
| JSON output stability                      | compatibility | JSON payload keys for stable commands remain backward compatible.               | al_quality_0100                  |
| Source tracking correctness                | correctness   | Source tracking reports file and impact deltas accurately.                      | al_quality_0097                  |

## Quality Scenarios

| Title                                                    | Quality         | Stimulus                                                                        | Response measure                                                                                               |
| -------------------------------------------------------- | --------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Build produces identical output for identical inputs     | reliability     | Runs archledger build twice on the same set of accepted records                 | Zero lines of diff between the two output files                                                                |
| Agent can create and validate records via CLI            | usability       | Agent creates a new black-box record and validates it via check --json          | Zero human interventions required; all operations complete via CLI invocations with exit code 0                |
| Native build does not require converters                 | portability     | User runs native markdown/asciidoc build on a clean Python environment.         | Exit code 0 and no converter invocation.                                                                       |
| Missing converter fails clearly                          | operability     | User requests PDF/DOCX without required converter installed.                    | Exit code non-zero with actionable diagnostic.                                                                 |
| Source tracking detects rename                           | traceability    | A tracked file is renamed with unchanged contents.                              | `source changed --json` includes at least one rename candidate with source/target paths and confidence >= 0.5. |
| Output path cannot escape build directory                | safety          | Config or CLI sets an escaping output path such as ../architecture.md.          | Invalid escaping output path causes non-zero exit and an error mentioning root-bound path validation.          |
| Agent can read model without build                       | usability       | Agent runs archledger read --json --body after source edits.                    | `archledger read --json --body` exits 0 and creates 0 build output files.                                      |
| Config v7 and source schema v2 records validate strictly | maintainability | Repository records include schema_version/date/body_format in source schema v2. | archledger check --strict exits 0.                                                                             |

# Risks and Technical Debt

Primary risks: documentation can drift from implementation (mitigated by source tracking, CI check integration, and `source_refs` on records), counter collisions when the storage metadata becomes stale (mitigated by the --repair-counters flag), and dependency on external converters (pandoc, asciidoctor) for non-native export formats which may not be available in all environments.

## Risk Overview

| Title                                                                | Severity | Probability | Mitigation                                                                                                                                                                                                                           | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| -------------------------------------------------------------------- | -------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Documentation drifts from implementation                             | medium   | medium      | Run archledger check in CI to detect stale or placeholder records. Use source tracking (snapshot/changed) to detect impacted records. Encourage agents to update records when modifying code and to maintain source_refs on records. | Architecture records describe the system at a point in time. As the codebase evolves, records may become stale or inaccurate. The `check` command detects placeholder text and missing fields, but cannot detect semantic drift. The source tracking subsystem (`snapshot`/`changed`) with `source_refs` on records provides file-level change-to-record linkage, enabling agents to identify which documentation needs updating when code changes. |
| Counter collisions on rapid record creation                          | medium   | medium      | Use archledger archive instead of deleting numbered fragments, and run archledger doctor --repair to restore missing IDs as tombstones and recompute storage.yaml next_number.                                                       | The storage metadata file tracks the next ledger number. If metadata becomes stale or numbered fragments are manually deleted, new records can collide with existing history. `archledger doctor --repair` recomputes `storage.yaml.next_number` and creates archive tombstones for missing non-section IDs so numbering stays gapless without renumbering existing records.                                                                        |
| External converter tools unavailable in CI or developer environments | medium   | low         | Native builds (Markdown-to-Markdown, AsciiDoc-to-AsciiDoc) require no external tools. Non-native formats fail gracefully with clear install instructions. CI can pre-install pandoc and asciidoctor gems.                            | The converter layer depends on external tools (pandoc, asciidoctor, asciidoctor-pdf) for non-native output formats. These tools may not be available in all environments. When a tool is missing, the build fails with a clear error message and installation instructions. Native builds always work without external dependencies.                                                                                                                |

# Glossary

Domain and technical terms used throughout the architecture documentation.

| Term                | Definition                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Architecture Record | A Markdown or AsciiDoc file with YAML front matter that describes one architecture element: a requirement, stakeholder, quality goal, constraint, context interface, strategy item, building block, runtime scenario, infrastructure, concept, ADR, quality requirement, quality scenario, risk, or glossary term.                                                              |
| arc42               | A template for architecture documentation created by Dr. Gernot Starke. It defines 12 sections: introduction and goals, constraints, context and scope, solution strategy, building block view, runtime view, deployment view, cross-cutting concepts, architecture decisions, quality requirements, risks and technical debt, and glossary. archledger follows this structure. |
| Front Matter        | The YAML block at the top of a Markdown record file, delimited by ---, containing machine-readable metadata fields. Parsed by archledger's frontmatter module to populate the ArchitectureRecord dataclass.                                                                                                                                                                     |
| Storage Directory   | The directory (configured as archledger_dir in archledger.toml) that holds the sections/, records/, build/ subdirectories and storage.yaml metadata file. Can be relative to the project root or an absolute external path.                                                                                                                                                     |
| Dialect             | A source format abstraction that defines how to render markup elements (headings, tables, bullets, strong text). archledger provides MarkdownDialect and AsciiDocDialect.                                                                                                                                                                                                       |
| Source Ref          | A traceability link from an architecture record to a source code artifact. Source refs have a path (relative to workspace root), optional symbols, and an optional reason. They enable change impact analysis.                                                                                                                                                                  |
| Source State        | A persisted source-tracking baseline with SHA-256 content hashes for tracked files plus derived directory hashes. Used by `archledger source changed` to detect modified, added, deleted, and possibly renamed files.                                                                                                                                                           |
