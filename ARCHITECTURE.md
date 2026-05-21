---
title: "Architecture Documentation"
date: "2026-05-21"
generator: "archledger 0.1.dev14+g542fa83a8.d19800101"
arc42_template_version: "9.0-EN"
---

# Architecture Documentation

Generated from archledger records. Do not edit this generated file directly.

# Introduction and Goals

archledger is a dual-source architecture documentation ledger for arc42-style documents. Both Markdown and AsciiDoc are first-class source formats. The tool keeps project-local configuration (`archledger.toml`) in the source workspace and stores human-editable architecture records as individual files with YAML front matter. The primary output is a rendered document assembled from these records, with optional exports to HTML, PDF, DOCX, RST, and Textile via pandoc or asciidoctor.

The tool targets three stakeholders: developers who document alongside code, architects who maintain the structural vision, and coding agents that automate documentation workflows via the CLI.

## Requirements Overview

<!-- archledger: no accepted records for this section yet -->

## Quality Goals

| Title | Priority | Scenario |
| --- | --- | --- |
| Maintainability | 1 | A developer can add a new record type with template, model mapping, and CLI alias in under 30 minutes, touching at most three files. |
| Reproducibility | 1 | Given the same set of accepted records, archledger build produces byte-identical output regardless of the host machine or locale. |
| Traceability | 1 | Every architecture record links to source evidence (file paths, CLI commands, test names) so that a reviewer can trace any documented decision back to code within two clicks. |

## Stakeholders

| Title | Contact | Expectations |
| --- | --- | --- |
| Coding Agent | None | JSON CLI output for machine parsing, Deterministic builds for CI pipelines, Seed preset for quick bootstrap, Skill file (SKILL.md) for agent protocol |
| Developer | None | Simple installation via pip, Clear CLI commands for init, new, check, build, Human-readable Markdown records easy to edit in any text editor |
| Architect | None | Structured arc42 sections with deterministic ordering, ADR records with Context/Decision/Consequences validation, Quality scenarios with measurable response measures, Cross-references between building blocks, ADRs, risks, and glossary terms |

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

## Business Context

<!-- archledger: no accepted records for this section yet -->

## Technical Context

- **Source repository** -> Source repository
  - The source repository hosts the `archledger.toml` config and the architecture record files. archledger reads records from disk and writes the rendered document back to the repository's build directory or a specified output path.
- **Coding agent harness** -> Coding Agent
  - Coding agents (pi, opencode, etc.) invoke archledger through its CLI, passing `--json` for machine-readable output. The agent skill file (`SKILL.md`) provides the protocol for how agents should interact with archledger: locate config, inspect records via `read`, detect changes via `source changed`, create/update in batches via `new`, validate with `check`, render with `build`, and persist baselines with `source snapshot`.
- **CI pipeline** -> CI runner
  - A CI runner can execute `archledger check` to validate record integrity and `archledger build` to produce the rendered document. Non-zero exit codes signal validation failures. The built Markdown can be published as a CI artifact or deployed to a documentation site.

# Solution Strategy

The fundamental approach is a file-based pipeline: human-editable Markdown or AsciiDoc records with YAML front matter are stored in a configurable directory, validated by a check command, assembled into a single arc42-style document by a Jinja2-based render step, and optionally converted to other formats (HTML, PDF, DOCX, RST, Textile) via pandoc or asciidoctor. A dialect abstraction (`dialects.py`) ensures that rendering logic works identically for both source formats. The CLI provides the sole interface. No server, database, or GUI is involved.

A source tracking subsystem (`source snapshot`/`source changed`) allows agents to detect which source files changed since the last baseline and which architecture records are impacted via `source_refs` linkage.

## Strategy Items

## File-based record pipeline with dual-source and multi-format export

**Drivers:** Maintainability, Traceability, Reproducibility
**Constraints:** Markdown or AsciiDoc with YAML front matter as canonical source, No external database dependency, Typer CLI interface
**Related ADRs:** adr0001, adr0002, adr0003

## Strategy

The core approach is a four-stage pipeline: author (create/edit Markdown or AsciiDoc records), validate (check integrity and completeness), assemble (render a single document using dialect-aware templates), and export (convert to requested formats via pandoc or asciidoctor). A source tracking subsystem enables change detection and impact analysis. A migration path allows converting from one source dialect to another. Each stage is independent and stateless except for the shared filesystem. The CLI orchestrates the pipeline and the Repository implements the business logic.

## Trade-offs

- Positive: simple mental model, easy to automate, no server dependency, supports both major documentation formats.
- Negative: no concurrent write protection, no real-time collaboration, referential integrity only checked on demand, external converter dependency for non-native formats.

# Building Block View

The system is decomposed into fifteen black boxes within a single white box. The CLI Layer receives user input and delegates output formatting, the Config Layer parses and renders project configuration, the Repository Layer orchestrates business logic, the Model Layer defines core data structures and validation, the Record Type Registry maps record types to templates and defaults, the Check Layer validates record content per type, the Source Ref Validation layer normalizes traceability links, the Storage Layer handles file I/O, the Assembly Layer renders the document via Jinja2 templates, the Dialect Layer abstracts format-specific markup, the Section Rendering Layer handles per-record-type output, the Render Layer orchestrates the build pipeline, the Converter Layer handles multi-format export, the Source Tracking Layer detects changes and impacts, and the Migration Layer converts between source dialects.

## Whitebox Overall System

## Motivation

archledger is decomposed into fifteen black boxes organized as a layered pipeline: the CLI accepts user input and delegates output formatting, the Config layer parses and renders project configuration, the Repository orchestrates business logic, the Model layer defines core data structures, the Record Type Registry maps record types to templates and defaults, the Check layer validates record content per type, the Source Ref Validation layer normalizes traceability links, the Storage layer handles file I/O, the Assembly layer renders the document, the Dialect layer abstracts format-specific markup, the Section Rendering layer handles per-record-type output, the Render layer orchestrates the build pipeline, the Converter layer handles multi-format export, the Source Tracking layer detects changes and impacts, and the Migration layer converts between source dialects.

## Contained building blocks

- **CLI Layer** (`cli.py`, `cli_formatting.py`, `cli_payloads.py`, `launcher.py`): Typer-based command-line interface with 11 top-level commands and a `source` subgroup (snapshot, changed, convert), JSON payload construction, and human-readable output formatting
- **Config Layer** (`config/`): Project configuration model, TOML parsing, default config rendering
- **Repository Layer** (`repository.py`): Business logic orchestration for init, create, list, check, status
- **Model Layer** (`model.py`, `errors.py`): Core data structures, validation constants, record lifecycle
- **Record Type Registry** (`record_types.py`): Record type specifications, directory/template/section mappings, CLI kind aliases
- **Check Layer** (`checks.py`): Per-record-type content validation and warning generation
- **Source Ref Validation** (`source_refs.py`): Traceability link normalization and path validation
- **Storage Layer** (`storage/`): File system access, front matter parsing, source state persistence
- **Assembly Layer** (`assembly.py`): Jinja2-based document assembly from records and sections
- **Dialect Layer** (`dialects.py`): Format-neutral markup abstraction (Markdown, AsciiDoc)
- **Section Rendering Layer** (`section_rendering.py`): Per-record-type rendering via dialects
- **Render Layer** (`render.py`): Build pipeline facade
- **Converter Layer** (`converters.py`, `conversion_plan.py`, `formats.py`): Multi-format export planning and execution via pandoc/asciidoctor
- **Source Tracking Layer** (`source_tracking.py`, `storage/source_state.py`): Change detection and impact analysis
- **Migration Layer** (`migration.py`): Source dialect conversion (Markdown to AsciiDoc)

## Important interfaces

The primary interface is the CLI (`archledger` console script). The CLI delegates to `cli_payloads.py` for JSON output construction and `cli_formatting.py` for human-readable messages. Internally, the Repository exposes methods that the CLI calls, and the Repository delegates to Storage, Model, Record Type Registry, Check, and Source Ref Validation. Config parsing is handled by the Config Layer independently from Storage. The Render Layer delegates to Assembly and Converters. The Converter Layer uses `conversion_plan.py` to plan each format conversion. Source Tracking is used by the CLI `source` subgroup for snapshot/changed/convert commands.

### Level 1

#### CLI Layer

**Parent:** white_box_0001
**Interfaces:** archledger console script (stdin/stdout)
**Location:** archledger/cli.py, archledger/cli_formatting.py, archledger/cli_payloads.py, archledger/launcher.py
**Fulfilled requirements:** **Risks:** 

The Typer-based CLI exposes top-level commands: `init`, `status`, `paths`, `schema`, `new`, `seed`, `list`, `show`, `read`, `check`, `build`, and the `source` subgroup. The `source` subgroup contains `snapshot`, `changed`, and `convert` for source tracking and dialect migration. Each command resolves the project config, constructs a Repository, and delegates to it. Two output modes are supported: human-readable text (default) and structured JSON (`--json` flag). Error handling maps domain exceptions (`ArchledgerError` subclasses) to appropriate exit codes and error output.

Output is split across three modules: `cli.py` defines Typer commands and dispatches to the Repository, `cli_payloads.py` constructs structured JSON dictionaries from domain result types, and `cli_formatting.py` renders human-readable messages from those payloads. This separation keeps the command definitions thin and testable.

The `source snapshot` and `source changed` commands integrate the source tracking subsystem. The `source convert` command delegates to the migration module for Markdown-to-AsciiDoc source conversion.

#### Repository Layer

**Parent:** white_box_0001
**Interfaces:** create_record(), list_records(), get_record(), load_all_records(), check(), init(), status()
**Location:** archledger/repository.py
**Fulfilled requirements:** **Risks:** 

The `ArchitectureRepository` class is the central business logic layer. It orchestrates record creation (allocating IDs via the Record Type Registry, rendering templates, writing files), record loading (parsing front matter, validating fields, normalizing source refs via the Source Ref Validation layer), integrity checks (delegating per-record-type content warnings to the Check Layer, plus cross-reference validation and source contract validation), and initialization (directory scaffolding, section file generation). It holds a Jinja2 environment for template rendering.

#### Render Layer

**Parent:** white_box_0001
**Interfaces:** build_document()
**Location:** archledger/render.py
**Fulfilled requirements:** **Risks:** 

The render module (`render.py`) is a thin facade that orchestrates the build pipeline. It resolves requested output formats via the formats module, delegates document assembly to the Assembly Layer, and then delegates multi-format conversion to the Converter Layer. The actual rendering logic is split across the Assembly Layer (template orchestration) and the Section Rendering Layer (per-record-type output).

#### Storage Layer

**Parent:** white_box_0001
**Interfaces:** read_text() / write_text(), read_markdown_front_matter(), resolve_project_paths(), read_source_state() / write_source_state()
**Location:** archledger/storage/common.py, archledger/storage/frontmatter.py, archledger/storage/meta.py, archledger/storage/paths.py, archledger/storage/source_state.py
**Fulfilled requirements:** **Risks:** 

The storage subpackage handles all file system I/O. `paths.py` discovers the project config and resolves directory layout (including `source_state_path` for tracking baselines). `project_config.py` holds the `ProjectConfig` dataclass with all configuration fields (source, build, arc42, skill, tracking). Config parsing and TOML loading now lives in the Config Layer (`config/` subpackage). `frontmatter.py` parses Markdown/AsciiDoc files with YAML front matter into metadata dict and body string, and provides `iter_source_files` for directory enumeration. `meta.py` manages the storage metadata file (`storage.yaml`). `source_state.py` reads and writes source tracking state as JSON. `common.py` provides `write_text`, `read_text`, `ensure_dir`, and `utc_now_iso`.

#### Model Layer

**Parent:** white_box_0001
**Interfaces:** ArchitectureRecord dataclass, SourceRef dataclass, validate_record(), filename_for(), record_sort_key(), normalize_kind()
**Location:** archledger/model.py, archledger/errors.py
**Fulfilled requirements:** **Risks:** 

The model module defines the core data structures and validation rules. `ArchitectureRecord` is a frozen dataclass holding id, type, title, status, section, order, path, metadata, body, and source_refs. `SourceRef` holds path, symbols, and reason for traceability linking. `validate_record()` checks field types, status values, and ID/filename consistency. Constants for valid formats, status values, and file extension mappings remain in `model.py`. Record type to directory/template/section mappings have been extracted to the Record Type Registry (`record_types.py`). Source ref validation and normalization have been extracted to the Source Ref Validation layer (`source_refs.py`). The `errors.py` module defines the exception hierarchy: `ArchledgerError` base with `ConfigError`, `StorageError`, `FrontMatterError`, `ValidationError`, and `RenderError` subclasses.

#### Assembly Layer

**Parent:** white_box_0001
**Interfaces:** assemble_document(), assemble_asciidoc_document()
**Location:** archledger/assembly.py
**Fulfilled requirements:** **Risks:** 

The assembly module loads all records from the repository, groups them by arc42 section, filters by visibility, selects the correct dialect, and renders a single document using a Jinja2 template (`arc42_document.md.j2` or `arc42_document.adoc.j2`). It delegates to the Section Rendering Layer for per-record-type output formatting. The assembly runs a check first and blocks the build if errors are found.

#### Dialect Layer

**Parent:** white_box_0001
**Interfaces:** get_dialect(), Dialect base class, MarkdownDialect / AsciiDocDialect
**Location:** archledger/dialects.py
**Fulfilled requirements:** **Risks:** 

The dialects module provides a format-neutral abstraction for document rendering. The `Dialect` base class defines methods for headings, tables, bullets, and strong text. `MarkdownDialect` and `AsciiDocDialect` implement these using the respective markup conventions (e.g., `#` vs `=` for headings, `|...|` vs `|===` tables). Both the Assembly Layer and Section Rendering Layer use dialects to produce format-correct output without conditional branching.

#### Section Rendering Layer

**Parent:** white_box_0001
**Interfaces:** section_body(), building_block_hierarchy(), adr_sections(), quality_scenarios(), risk_table(), glossary_table(), (and other per-type renderers)
**Location:** archledger/section_rendering.py
**Fulfilled requirements:** **Risks:** 

The section rendering module contains all per-record-type rendering functions. Each function takes a list of `ArchitectureRecord` and a `Dialect`, and returns a format-appropriate string (Markdown or AsciiDoc). Functions include table renderers (quality goals, stakeholders, quality scenarios, risks, glossary), list renderers (constraints, context interfaces), hierarchy renderers (building blocks with white/black boxes and interfaces), and prose renderers (ADRs, runtime scenarios, deployment, concepts, strategy items).

#### Converter Layer

**Parent:** white_box_0001
**Interfaces:** convert_assembled_document()
**Location:** archledger/converters.py, archledger/conversion_plan.py, archledger/formats.py
**Fulfilled requirements:** **Risks:** 

The converter module handles multi-format export. It takes an assembled document (from the Assembly Layer) and produces output in the requested formats. For native format builds (Markdown source to Markdown output, or AsciiDoc source to AsciiDoc output), it does a direct file copy. For other formats, it invokes external converters: pandoc for Markdown-to-HTML/PDF/DOCX/RST/Textile, asciidoctor for AsciiDoc-to-HTML/PDF (direct or via DocBook intermediate), and pandoc for AsciiDoc-to-DOCX/Markdown/RST/Textile (via DocBook). The formats module (`formats.py`) defines the `OutputFormat` enum and resolves requested formats from CLI options and config.

Conversion planning is handled by `conversion_plan.py`, which produces a `ConversionPlan` dataclass for each requested format. Each plan specifies whether the conversion is a native copy, a direct tool invocation, or requires a DocBook intermediate step. Tool resolution uses `shutil.which` by default. The `require_tool()` function raises `RenderError` with install hints when a required converter is unavailable. DocBook intermediates are cleaned up unless `build_keep_intermediate` is set.

#### Source Tracking Layer

**Parent:** white_box_0001
**Interfaces:** scan_workspace(), diff_source_states(), resolve_impacts()
**Location:** archledger/source_tracking.py, archledger/storage/source_state.py
**Fulfilled requirements:** **Risks:** 

The source tracking module detects changes between a baseline snapshot and the current workspace state. `scan_workspace` enumerates all tracked files using git or filesystem scanning, computes SHA-256 hashes, and records file sizes and mtimes. `diff_source_states` compares two snapshots to produce a `ChangeSet` listing added, modified, and deleted files with possible rename detection. `resolve_impacts` cross-references changed files with architecture record `source_refs` to identify which records and sections are impacted by the changes, and which changed files have no linked records.

The storage sub-module (`storage/source_state.py`) handles JSON serialization and deserialization of the source state, persisted alongside `storage.yaml`.

#### Migration Layer

**Parent:** white_box_0001
**Interfaces:** convert_sources()
**Location:** archledger/migration.py
**Fulfilled requirements:** **Risks:** 

The migration module converts source fragments from one dialect to another. Currently supports Markdown-to-AsciiDoc conversion. It iterates over all section and record files, converts the body using pandoc (falling back to keeping the original body if pandoc is unavailable), updates the YAML front matter to reflect the new body format, and optionally replaces the original files. It also rewrites the project config to target the new source format.

#### Config Layer

**Parent:** white_box_0001
**Interfaces:** load_project_config(), render_default_config(), ProjectConfig dataclass
**Location:** archledger/config/__init__.py, archledger/config/model.py, archledger/config/parse.py, archledger/config/render.py
**Fulfilled requirements:** **Risks:** 

The `config` subpackage owns all project configuration concerns. `config/model.py` defines frozen dataclasses for each configuration domain: `SourceConfig`, `BuildConfig` (with nested `BuildOutputConfig`), `Arc42Config`, `SkillConfig`, `TrackingConfig`, and the unified `ProjectConfig` facade that composes them via properties. `config/parse.py` loads and validates `archledger.toml` using `tomllib` (or `tomli` for Python < 3.11), with strict key validation and environment variable expansion. `config/render.py` generates default configuration files for `archledger init`. The subpackage re-exports key types from `__init__.py`.

#### Record Type Registry

**Parent:** white_box_0001
**Interfaces:** RECORD_TYPES registry, CLI_KIND_ALIASES, RecordTypeSpec dataclass
**Location:** archledger/record_types.py
**Fulfilled requirements:** **Risks:** 

The `record_types.py` module is the central registry for all arc42 record types. It defines `RecordTypeSpec`, a frozen dataclass mapping each record kind to its directory name, filename prefix, default section, template basename, CLI aliases, default status/level, and a context factory function. The `RECORD_TYPES` dictionary provides the authoritative lookup. `CLI_KIND_ALIASES` maps alternative names (e.g., `qg` for `quality_goal`) for the CLI. This module was extracted from `model.py` to keep the model focused on data structures while record type configuration lives in one discoverable location.

#### Check Layer

**Parent:** white_box_0001
**Interfaces:** content_warnings()
**Location:** archledger/checks.py
**Fulfilled requirements:** **Risks:** 

The `checks.py` module provides per-record-type content validation beyond structural checks. The main entry point is `content_warnings()`, which returns a list of warning strings for a given `ArchitectureRecord`. It dispatches to type-specific checkers registered in `_CONTENT_WARNING_CHECKERS`: quality goals require scenarios, stakeholders require expectations, constraints require impact and valid categories, ADRs require Context/Decision/Consequences sections and deciders, quality scenarios require measurable response measures, risks require valid severity/probability and mitigation, and so on. It also detects placeholder text in record bodies and cross-dialect syntax contamination (e.g., AsciiDoc headings in Markdown records). This module was extracted from `repository.py` to isolate validation logic.

#### Source Ref Validation

**Parent:** white_box_0001
**Interfaces:** normalize_source_refs(), validate_relative_posix_path()
**Location:** archledger/source_refs.py
**Fulfilled requirements:** **Risks:** 

The `source_refs.py` module handles validation and normalization of source traceability links on architecture records. `validate_relative_posix_path()` enforces that source ref paths are relative, use POSIX separators, and do not traverse parent directories. `normalize_source_refs()` processes the raw `source_refs` list from YAML front matter, supporting both shorthand string syntax (`path/to/file.py#SymbolName`) and full mapping syntax with explicit path, symbols, and reason. It verifies that referenced paths and directories actually exist in the workspace. `RelativePosixPathError` provides structured error reporting for invalid paths. This module was extracted from `model.py` to keep source ref validation independent from the core data model.

# Runtime View

Key runtime scenarios: initializing a new project (scaffolding directories and section files), creating and rendering records (the primary authoring flow), validating records with check (ensuring consistency and completeness), building multi-format output (assembly plus optional conversion), taking source snapshots and detecting changes (source tracking), and converting source dialects (Markdown to AsciiDoc migration).

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
2. CLI renders the default TOML config with a generated project UUID, name derived from the directory, and source format from the `--source-format` option (defaults to `asciidoc`).
3. CLI writes the config file and resolves project paths.
4. Repository creates the archledger_dir, sections_dir, records_dir, and build_dir.
5. Repository creates 15 record subdirectories (one per record type directory).
6. Repository writes 12 section Markdown files (01_introduction_and_goals through 12_glossary) with section extensions matching the configured source format.
7. Repository writes the storage.yaml metadata file.
8. The project is ready for `archledger new` commands.

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

# Deployment View

archledger runs as a local CLI tool on developer machines and in CI runners. There is no server component. The storage directory can be co-located with the source repository or placed in an external path via configuration.

## Local development

Developer machine with Python >= 3.10. archledger is installed via `pip install -e .` in a virtual environment. The project directory contains `archledger.toml` at the root. The storage directory (default `.archledger/`) holds sections, records, and build output. No network access, database, or server process is required.

## CI pipeline

CI runners execute `archledger check` to validate record integrity and `archledger build --output docs/architecture.md` to produce the rendered document. The built Markdown file is published as a CI artifact. Non-zero exit codes from `check` fail the pipeline.

# Cross-cutting Concepts

Three cross-cutting concepts pervade the architecture: the record lifecycle (draft, proposed, accepted, deprecated, superseded) which controls visibility and validation behavior, the config discovery mechanism which resolves project paths from the workspace directory upward, and the dialect abstraction which ensures format-neutral rendering for both Markdown and AsciiDoc sources.

## Record lifecycle and status

Every record has a status field that controls its lifecycle: `draft` (incomplete, excluded from default builds), `proposed` (visible but not formally confirmed), `accepted` (confirmed, included by default), `deprecated` (visible but no longer preferred), and `superseded` (hidden unless explicitly included). The `check` command warns about draft records and empty sections. The `build` command only includes records with visible statuses by default; `--include-draft` and `--include-superseded` flags override this.

## Config discovery and path resolution

archledger discovers its project configuration by walking up from the current directory looking for `archledger.toml` or `.archledger.toml`. The `archledger_dir` setting in the config can be relative (resolved from the config file's directory) or absolute (used as-is). This allows the storage directory to live outside the source tree, for example in a separate state repository.

Config parsing is handled by the Config Layer (`config/` subpackage): `config/parse.py` loads and validates the TOML file, `config/model.py` defines typed dataclasses for each configuration domain (source, build, arc42, skill, tracking), and `config/render.py` generates default configuration files for `archledger init`. Path resolution happens in `storage/paths.py`.

## Dialect abstraction for dual-source support

archledger supports both Markdown and AsciiDoc as first-class source formats. The dialect abstraction (`dialects.py`) defines a `Dialect` base class with methods for headings, tables, bullets, and strong text. `MarkdownDialect` and `AsciiDocDialect` implement these using their respective markup conventions. All rendering code in the Section Rendering Layer and Assembly Layer uses dialects rather than hardcoded markup, ensuring that a single rendering codebase produces correct output for both source formats. Templates exist in both `.md.j2` and `.adoc.j2` variants.

## Source tracking and change impact analysis

The source tracking subsystem allows agents to detect which workspace files changed since the last baseline snapshot and which architecture records are impacted. A snapshot (`archledger source snapshot`) records SHA-256 hashes of all tracked files. The `source changed` command computes the diff between the baseline and current state, then cross-references changed files with record `source_refs` to identify impacted records and sections. Files that changed but have no linked records are reported as unlinked. This enables agents to update only the documentation affected by code changes.

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

# Quality Requirements

The top quality scenarios address deterministic builds and agent-friendly CLI interaction. These directly support the quality goals of reproducibility, maintainability, and traceability.

## Quality Requirements Overview

<!-- archledger: no accepted records for this section yet -->

## Quality Scenarios

| Title | Quality | Stimulus | Response measure |
| --- | --- | --- | --- |
| Build produces identical output for identical inputs | reliability | Runs archledger build twice on the same set of accepted records | Zero lines of diff between the two output files |
| Agent can create and validate records via CLI | usability | Agent creates a new black-box record and validates it via check --json | Zero human interventions required; all operations complete via CLI invocations with exit code 0 |

# Risks and Technical Debt

Primary risks: documentation can drift from implementation (mitigated by source tracking, CI check integration, and `source_refs` on records), counter collisions when the storage metadata becomes stale (mitigated by the --repair-counters flag), and dependency on external converters (pandoc, asciidoctor) for non-native export formats which may not be available in all environments.

## Risk Overview

| Title | Severity | Probability | Mitigation | Notes |
| --- | --- | --- | --- | --- |
| Documentation drifts from implementation | medium | medium | Run archledger check in CI to detect stale or placeholder records. Use source tracking (snapshot/changed) to detect impacted records. Encourage agents to update records when modifying code and to maintain source_refs on records. | Architecture records describe the system at a point in time. As the codebase evolves, records may become stale or inaccurate. The `check` command detects placeholder text and missing fields, but cannot detect semantic drift. The source tracking subsystem (`snapshot`/`changed`) with `source_refs` on records provides file-level change-to-record linkage, enabling agents to identify which documentation needs updating when code changes. |
| Counter collisions on rapid record creation | medium | medium | Run archledger check --repair-counters to recompute counters from existing files. Always run repair-counters after counter anomalies. | The storage metadata file tracks next-number counters for each record type prefix. If the metadata becomes stale (e.g., after manual file operations or rapid concurrent creation), new records may receive colliding IDs or filenames. The `--repair-counters` flag on `check` recomputes counters from the actual files on disk. |
| External converter tools unavailable in CI or developer environments | medium | low | Native builds (Markdown-to-Markdown, AsciiDoc-to-AsciiDoc) require no external tools. Non-native formats fail gracefully with clear install instructions. CI can pre-install pandoc and asciidoctor gems. | The converter layer depends on external tools (pandoc, asciidoctor, asciidoctor-pdf) for non-native output formats. These tools may not be available in all environments. When a tool is missing, the build fails with a clear error message and installation instructions. Native builds always work without external dependencies. |

# Glossary

Domain and technical terms used throughout the architecture documentation.

| Term | Definition |
| --- | --- |
| Architecture Record | A Markdown or AsciiDoc file with YAML front matter that describes one architecture element: a requirement, stakeholder, quality goal, constraint, context interface, strategy item, building block, runtime scenario, infrastructure, concept, ADR, quality requirement, quality scenario, risk, or glossary term. |
| arc42 | A template for architecture documentation created by Dr. Gernot Starke. It defines 12 sections: introduction and goals, constraints, context and scope, solution strategy, building block view, runtime view, deployment view, cross-cutting concepts, architecture decisions, quality requirements, risks and technical debt, and glossary. archledger follows this structure. |
| Front Matter | The YAML block at the top of a Markdown record file, delimited by ---, containing machine-readable metadata fields. Parsed by archledger's frontmatter module to populate the ArchitectureRecord dataclass. |
| Storage Directory | The directory (configured as archledger_dir in archledger.toml) that holds the sections/, records/, build/ subdirectories and storage.yaml metadata file. Can be relative to the project root or an absolute external path. |
| Dialect | A source format abstraction that defines how to render markup elements (headings, tables, bullets, strong text). archledger provides MarkdownDialect and AsciiDocDialect. |
| Source Ref | A traceability link from an architecture record to a source code artifact. Source refs have a path (relative to workspace root), optional symbols, and an optional reason. They enable change impact analysis. |
| Source State | A persisted snapshot of all tracked workspace files with their SHA-256 hashes, sizes, and modification times. Used as the baseline for change detection. |
