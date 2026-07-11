---
title: "archledger Architecture Documentation"
version: 2
generator: "archledger 0.3.2.dev1+g505ad5c4c"
arc42_template_version: "9.0-EN"
---

# archledger Architecture Documentation

Generated from archledger records. Do not edit this generated file directly.

# Introduction and Goals

archledger is a source-first architecture documentation ledger for arc42-style
documents. Markdown and AsciiDoc are first-class source formats. Project-local
configuration selects the storage paths, while human-editable architecture
records use YAML front matter and versioned bodies. Native builds assemble these
records directly; optional converters produce HTML, PDF, DOCX, RST, or Textile.

The tool targets developers, architects, and coding agents. Its scope is
architecture records, links, and source evidence. Behavior specifications are
maintained by SpecMason, and lifecycle or cross-ledger orchestration remains
outside Archledger.

## How to update this architecture

Use the source-first maintenance loop:

```bash
archledger --json source changed
archledger --json context --changed
archledger record export RECORD_ID --output /tmp/record.md
# edit /tmp/record.md
archledger record apply RECORD_ID --from-file /tmp/record.md
archledger --json check --strict
archledger --json source snapshot --reason after-archledger-update
```

Detailed agent guidance lives in `docs/agent-workflow.md`.

## Requirements Overview

| Title                                                                | Priority | Source                                                | Stakeholders | Quality goals |
| -------------------------------------------------------------------- | -------- | ----------------------------------------------------- | ------------ | ------------- |
| Project initialization creates archledger workspace structure        | must     | archledger CLI behavior and repository implementation |              |               |
| File-based source model uses editable records                        | must     | archledger CLI behavior and repository implementation |              |               |
| Record creation enforces schema and unique ids                       | must     | archledger CLI behavior and repository implementation |              |               |
| Read current architecture model without export                       | must     | archledger CLI behavior and repository implementation |              |               |
| Native build requires no external converter tools                    | must     | archledger CLI behavior and repository implementation |              |               |
| Multi-format export supports configured converter tools              | must     | archledger CLI behavior and repository implementation |              |               |
| Source tracking reports changes impacts and unlinked files           | must     | archledger CLI behavior and repository implementation |              |               |
| Path safety prevents writes outside allowed roots                    | must     | archledger CLI behavior and repository implementation |              |               |
| CLI provides stable machine-readable JSON output                     | must     | archledger CLI behavior and repository implementation |              |               |
| Local-first operation requires no network services                   | must     | archledger CLI behavior and repository implementation |              |               |
| Agent context and trace queries return focused architecture evidence | must     | Agent context and trace implementation                |              |               |

## Quality Goals

| Title           | Priority | Scenario                                                                                                                                                                       |
| --------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Maintainability | 1        | A developer can add a new record type with template, model mapping, and CLI alias in under 30 minutes, touching at most three files.                                           |
| Reproducibility | 1        | Given the same set of accepted records, archledger build produces byte-identical output regardless of the host machine or locale.                                              |
| Traceability    | 1        | Every architecture record links to source evidence (file paths, CLI commands, test names) so that a reviewer can trace any documented decision back to code within two clicks. |

## Stakeholders

| Title        | Contact                              | Expectations                                                                                                                                                                                                                                     |
| ------------ | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Coding Agent | Project repository and agent harness | JSON CLI output for machine parsing, Deterministic builds for CI pipelines, Seed preset for quick bootstrap, Skill file (SKILL.md) for agent protocol                                                                                            |
| Developer    | Project repository                   | Simple installation via pip, Clear CLI commands for init, new, check, build, Human-readable Markdown records easy to edit in any text editor                                                                                                     |
| Architect    | Project repository                   | Structured arc42 sections with deterministic ordering, ADR records with Context/Decision/Consequences validation, Quality scenarios with measurable response measures, Cross-references between building blocks, ADRs, risks, and glossary terms |

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
- **Archledger remains an isolated architecture ledger**
  - Impact: Archledger stores only architecture records, links, and source evidence; behavior specifications and cross-ledger workflow policy remain external.
  - Notes: Archledger is the source-first ledger for architecture records, arc42 sections,
    record links, and source or test evidence. It does not own behavior-specification
    artifacts, execute BDD workflows, enforce software-development lifecycle policy,
    or interpret relationships between independent ledgers.

External artifacts may be referenced through opaque links or source references.
Semantic coordination belongs to an external organizer. Behavior specifications
in this repository are maintained by SpecMason and remain outside the
Archledger record model.

This boundary keeps architecture validation deterministic and prevents
Archledger from becoming a general workflow orchestrator.

# Context and Scope

Archledger interacts with the source repository, developers and coding agents,
CI pipelines, and optional document converters. All communication uses local
filesystem access, process I/O, or converter subprocesses. The CLI returns human
text or stable JSON envelopes for automation.

Behavior specifications and other ledgers are external systems. Archledger may
preserve opaque links or source references to their artifacts, but it does not
execute their workflows or interpret cross-ledger semantics. SpecMason owns the
repository's behavior specifications.

See the [System Context diagram](#diagram-al_diagram_0035) for a visual overview
of actors and system boundaries.

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

The fundamental approach is a file-based pipeline: human-editable Markdown or
AsciiDoc records with YAML front matter are validated, assembled into an arc42
document with Jinja2, and optionally converted through pandoc or asciidoctor. A
dialect abstraction keeps rendering independent of the source format. The CLI
is the sole product interface; there is no server, database, or GUI.

A typed record registry describes per-record metadata shapes. Existing records
are changed through version-aware mutation commands. Complete-document apply
operations validate identity and kind, increment versions only for real changes,
and roll back the target when repository validation fails.

Source tracking compares the workspace with an explicit snapshot and maps
changed files to architecture records through `source_refs`. Focused context and
trace queries expose bounded architecture evidence without requiring a build.
Archledger deliberately remains isolated from behavior-specification and
cross-ledger workflow semantics.

## Strategy Items

## File-based record pipeline with dual-source and multi-format export

**Drivers:** Maintainability, Traceability, Reproducibility
**Constraints:** Markdown or AsciiDoc with YAML front matter as canonical source, No external database dependency, Typer CLI interface
**Related ADRs:** adr-0077, adr-0078, adr-0079

## Strategy

The core approach is a four-stage pipeline: author (create/edit Markdown or AsciiDoc records), validate (check integrity and completeness), assemble (render a single document using dialect-aware templates), and export (convert to requested formats via pandoc or asciidoctor). A source tracking subsystem enables change detection and impact analysis. A migration path allows converting from one source dialect to another. Each stage is independent and stateless except for the shared filesystem. The CLI orchestrates the pipeline and the Repository implements the business logic.

## Trade-offs

- Positive: simple mental model, easy to automate, no server dependency, supports both major documentation formats.
- Negative: no concurrent write protection, no real-time collaboration, referential integrity only checked on demand, external converter dependency for non-native formats.

# Building Block View

The system is one white box composed of focused services. The CLI layer parses
commands and presents human or JSON results. Config and Storage resolve project
paths and persist front-matter records. Repository and Model load records and
enforce structural, metadata-shape, and cross-reference rules. The Record Type
Registry supplies type-specific metadata contracts and templates. The Record
Mutation Service performs versioned, validated writes with rollback.

Assembly, Dialect, Section Rendering, Render, and Converter services build native
or converted documents. Source Tracking reports drift and impact. Context and
Trace provide bounded architecture evidence. Migration, identity, renumbering,
ID sequence, and segment services preserve source-model integrity. Diagram,
source-ref, test-ref, link, scope, and check services validate specialized
contracts.

See the [Building Block Layer Structure diagram](#diagram-al_diagram_0040) for a
visual decomposition of the principal layer relationships.

## Building Block Layer Structure

The CLI coordinates read paths through the Repository and write paths through
the Record Mutation Service. Shared model and registry contracts govern both.
Rendering and evidence-query services consume the same canonical storage.

```textdiagram
┌─ Interface ───────────────────────────────────────────────────┐
│ CLI, payload formatting, human formatting                    │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Source-model services ───────────────────────────────────────┐
│ Repository │ Model │ Record Types │ Checks │ Mutations        │
│ Source refs │ Test refs │ Links │ Scopes │ ID services       │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Persistence and configuration ───────────────────────────────┐
│ Config │ Front matter │ Storage │ Archive │ Source state      │
└───────────────┬─────────────────────────────┬─────────────────┘
                ▼                             ▼
┌─ Document pipeline ────────────┐  ┌─ Evidence pipeline ──────┐
│ Assembly │ Dialects │ Sections │  │ Source Tracking          │
│ Render │ Diagrams │ Converters │  │ Context │ Trace │ Combo  │
└───────────────┬────────────────┘  └───────────────────────────┘
                ▼
       Native document and optional exports
```

**Caption:** Layered decomposition of archledger building blocks

## Whitebox Overall System

## Motivation

Archledger is decomposed into focused services within one source-first
architecture ledger. The package separates CLI presentation, repository and
model validation, storage, record mutation, rendering, conversion, source
tracking, and evidence queries. Behavior specifications and cross-ledger
workflow semantics are explicit external concerns.

## Principal building blocks

- **CLI and payload formatting**: Typer commands, human output, and stable JSON
  envelopes.
- **Config, Storage, Repository, and Model**: path resolution, front-matter I/O,
  orchestration, record loading, typed metadata validation, and references.
- **Record Type Registry and Record Mutation Service**: type-specific metadata
  contracts, templates, versioned writes, complete-document apply, and rollback.
- **Check, source-ref, test-ref, link, and scope services**: specialized source
  model validation and traceability.
- **Assembly, Dialect, Section Rendering, Render, Diagram, and Converter
  services**: native document construction and optional external conversion.
- **Source Tracking, Context, Trace, and combo trace**: drift detection, bounded
  record selection, and evidence traversal.
- **Migration, identity, ledger sequence, ID segment, and Renumber services**:
  safe evolution of source format and record identity.

## Important interfaces

The `archledger` CLI is the product interface. It delegates reads and checks to
the repository, writes to the Record Mutation Service, and rendering to the
assembly and converter path. Config parsing and storage remain independent of
presentation. Source Tracking feeds changed-file context queries. Context and
Trace return architecture evidence only; they do not coordinate behavior specs
or external ledgers.

### Level 1

#### CLI Layer

**Parent:** block-0041
**Interfaces:** archledger console script (stdin/stdout)
**Location:** archledger/cli.py, archledger/cli_formatting.py, archledger/cli_payloads.py, archledger/launcher.py

The Typer-based CLI exposes project setup and inspection (`init`, `status`,
`paths`, `schema`, `list`, `show`, `read`), lifecycle and integrity operations
(`new`, `seed`, `check`, `archive`, `doctor`, `renumber`), document builds,
focused `context` and `trace`, and grouped commands for source tracking,
migration, profiles, record mutations, references, links, acceptance criteria,
and scopes.

Commands resolve project configuration, invoke domain services, and return
human-readable output or a stable JSON envelope selected by the root `--json`
option. `cli_payloads.py` shapes reusable payloads and `cli_formatting.py`
formats human output.

Record mutation commands accept typed metadata through positional compatibility,
`--json-value`, `--string-value`, or `--from-file`. `record export` and `record apply` support complete-document editing. Every target mutation snapshots the
original text, validates the result through the Repository, and restores the
original on failure. Source migration and ID renumbering retain explicit dry-run
or apply boundaries for destructive changes.

#### Repository Layer

**Parent:** block-0041
**Interfaces:** create_record(), list_records(), get_record(), load_all_records(), check(), init(), status()
**Location:** archledger/repository.py

The `ArchitectureRepository` class is the central business logic layer. It orchestrates record creation (allocating IDs via the Record Type Registry using the configured `LedgerIdFormat` and segment resolution from `id_segments.py`, rendering templates, writing files), record loading (parsing front matter, validating fields including ID syntax and segment expectations, normalizing source refs via the Source Ref Validation layer), integrity checks (delegating per-record-type content warnings to the Check Layer, plus cross-reference validation and source contract validation), and initialization (directory scaffolding, section file generation with init-time ID format options). It holds a Jinja2 environment for template rendering.

Record ID allocation uses `ProjectConfig.id_format` to format the next number with the configured prefix, width, and segment. In segmented mode, the segment is resolved via `id_segment_for_new_record()` from the record kind and config `segment_map`.

#### Render Layer

**Parent:** block-0041
**Interfaces:** build_document()
**Location:** archledger/render.py

The render module (`render.py`) is a thin facade that orchestrates the build pipeline. It resolves requested output formats via the formats module, delegates document assembly to the Assembly Layer, and then delegates multi-format conversion to the Converter Layer. The actual rendering logic is split across the Assembly Layer (template orchestration) and the Section Rendering Layer (per-record-type output).

#### Storage Layer

**Parent:** block-0041
**Interfaces:** read_text() / write_text(), read_markdown_front_matter(), resolve_project_paths(), read_source_state() / write_source_state()
**Location:** archledger/storage/common.py, archledger/storage/frontmatter.py, archledger/storage/meta.py, archledger/storage/paths.py, archledger/storage/source_state.py

The storage subpackage handles all file system I/O. `paths.py` discovers the project config and resolves directory layout (including `source_state_path` for tracking baselines). `project_config.py` holds the `ProjectConfig` dataclass with all configuration fields (source, build, arc42, skill, tracking). Config parsing and TOML loading now lives in the Config Layer (`config/` subpackage). `frontmatter.py` parses Markdown/AsciiDoc files with YAML front matter into metadata dict and body string, and provides `iter_source_files` for directory enumeration. `meta.py` manages the storage metadata file (`storage.yaml`). `source_state.py` reads and writes source tracking state as JSON. `common.py` provides `write_text`, `read_text`, `ensure_dir`, and `utc_now_iso`.

#### Model Layer

**Parent:** block-0041
**Interfaces:** ArchitectureRecord dataclass, SourceRef dataclass, validate_record(), validate_record_metadata_shape(), filename_for(), record_sort_key(), normalize_kind()
**Location:** archledger/model.py, archledger/errors.py

The Model Layer defines immutable architecture records, normalized source
references, validation constants, and core record invariants. `validate_record()`
checks field types, lifecycle status, identifier and filename consistency, and
segment expectations.

Metadata-shape validation obtains field specifications from the Record Type
Registry and verifies strings, integers, booleans, string lists, objects, and
object lists. Diagnostics identify the record and field, report the observed
shape, and provide a typed `record meta set` repair example. Archive tombstones
and section records use their dedicated contracts.

Specialized source-reference validation remains in `source_refs.py`; record type
definitions remain in `record_types.py`; domain exceptions remain in
`errors.py`.

#### Assembly Layer

**Parent:** block-0041
**Interfaces:** assemble_document(), assemble_asciidoc_document()
**Location:** archledger/assembly.py

The assembly module loads all records from the repository, groups them by arc42 section, filters by visibility, selects the correct dialect, and renders a single document using a Jinja2 template (`arc42_document.md.j2` or `arc42_document.adoc.j2`). It delegates to the Section Rendering Layer for per-record-type output formatting. The assembly runs a check first and blocks the build if errors are found.

#### Dialect Layer

**Parent:** block-0041
**Interfaces:** get_dialect(), Dialect base class, MarkdownDialect / AsciiDocDialect
**Location:** archledger/dialects.py

The dialects module provides a format-neutral abstraction for document rendering. The `Dialect` base class defines methods for headings, tables, bullets, and strong text. `MarkdownDialect` and `AsciiDocDialect` implement these using the respective markup conventions (e.g., `#` vs `=` for headings, `|...|` vs `|===` tables). Both the Assembly Layer and Section Rendering Layer use dialects to produce format-correct output without conditional branching.

#### Section Rendering Layer

**Parent:** block-0041
**Interfaces:** section_body(), building_block_hierarchy(), adr_sections(), quality_scenarios(), risk_table(), glossary_table(), (and other per-type renderers)
**Location:** archledger/section_rendering.py

The section rendering module contains all per-record-type rendering functions. Each function takes a list of `ArchitectureRecord` and a `Dialect`, and returns a format-appropriate string (Markdown or AsciiDoc). Functions include table renderers (quality goals, stakeholders, quality scenarios, risks, glossary), list renderers (constraints, context interfaces), hierarchy renderers (building blocks with white/black boxes and interfaces), and prose renderers (ADRs, runtime scenarios, deployment, concepts, strategy items).

#### Converter Layer

**Parent:** block-0041
**Interfaces:** convert_assembled_document()
**Location:** archledger/converters.py, archledger/conversion_plan.py, archledger/formats.py

The converter module handles multi-format export. It takes an assembled document (from the Assembly Layer) and produces output in the requested formats. For native format builds (Markdown source to Markdown output, or AsciiDoc source to AsciiDoc output), it does a direct file copy. For other formats, it invokes external converters: pandoc for Markdown-to-HTML/PDF/DOCX/RST/Textile, asciidoctor for AsciiDoc-to-HTML/PDF (direct or via DocBook intermediate), and pandoc for AsciiDoc-to-DOCX/Markdown/RST/Textile (via DocBook). The formats module (`formats.py`) defines the `OutputFormat` enum and resolves requested formats from CLI options and config.

Conversion planning is handled by `conversion_plan.py`, which produces a `ConversionPlan` dataclass for each requested format. Each plan specifies whether the conversion is a native copy, a direct tool invocation, or requires a DocBook intermediate step. Tool resolution uses `shutil.which` by default. The `require_tool()` function raises `RenderError` with install hints when a required converter is unavailable. DocBook intermediates are cleaned up unless `build_keep_intermediate` is set.

#### Source Tracking Layer

**Parent:** block-0041
**Interfaces:** scan_workspace(), diff_source_states(), resolve_impacts()
**Location:** archledger/source_tracking.py, archledger/storage/source_state.py

The source tracking module detects changes between a baseline snapshot and the current workspace state. `scan_workspace` enumerates tracked files using git or filesystem scanning, computes SHA-256 content hashes, and stores SHA-256-only file entries. It also derives directory hashes and file counts from the scanned file tree. `diff_source_states` compares two snapshots to produce a `ChangeSet` listing added, modified, and deleted files with possible rename detection. `resolve_impacts` cross-references changed files with architecture record `source_refs` to identify impacted records and unlinked changed files.

The storage sub-module (`storage/source_state.py`) handles JSON serialization and deserialization of the source state, persisted alongside `storage.yaml`.

#### Migration Layer

**Parent:** block-0041
**Interfaces:** convert_sources()
**Location:** archledger/migration.py

The migration module converts source fragments from one dialect to another. Currently supports Markdown-to-AsciiDoc conversion. It iterates over all section and record files, converts the body using pandoc (falling back to keeping the original body if pandoc is unavailable), updates the YAML front matter to reflect the new body format, and optionally replaces the original files. It also rewrites the project config to target the new source format. Migration was updated to handle configurable ID format fields during config rewriting.

#### Config Layer

**Parent:** block-0041
**Interfaces:** load_project_config(), build_default_project_config(), render_project_config(), ProjectConfig dataclass
**Location:** archledger/config/**init**.py, archledger/config/model.py, archledger/config/parse.py, archledger/config/render.py

The `config` subpackage owns all project configuration concerns. `config/model.py` defines frozen dataclasses for each configuration domain: `SourceConfig`, `BuildConfig` (with nested `BuildOutputConfig`), `Arc42Config`, `SkillConfig`, `TrackingConfig`, and the unified `ProjectConfig` facade that composes them via properties. It also exports public allowed-value constants (`VALID_BUILD_CONVERTERS`, `VALID_DIAGRAM_RENDERERS`, `VALID_DIAGRAM_TYPES`, `VALID_DIAGRAM_IMAGE_FORMATS`, `VALID_TRACKING_SCANNERS`) shared by `parse.py`, `render.py`, and `cli.py`.

`ProjectConfig` includes ID format fields: `id_prefix` (default `al`), `id_width` (default `4`), `id_segment_mode` (default `none`), `id_default_segment`, and `id_segment_map`. The `id_format` property constructs a `LedgerIdFormat` instance from these fields, providing the canonical ID formatting object used throughout the repository, check, and renumber layers.

`config/parse.py` loads and validates `archledger.toml` using `tomllib` (or `tomli` for Python < 3.11), with strict key validation and environment variable expansion. It parses the `[ids]` section, validating prefix, width, segment mode, and segment map using validators from `ids.py`. `config/render.py` generates default configuration files for `archledger init` via a two-stage pipeline: `build_default_project_config()` constructs a validated `ProjectConfig` dataclass from init parameters (including build, diagram, arc42, tracking, and ID format options), and `render_project_config()` serializes it to TOML.

The `[diagrams]` section supports five diagram types (`text`, `ascii`, `unicode`, `svgbob`, `mermaid`) and three renderers (`pass-through`, `mermaid-cli`, `asciidoctor-diagram`). The default diagram type is `text`, ensuring that new diagram records produce readable text-based diagrams in native builds without any external tooling.

The `[ids]` section (config version 7+) configures the ledger ID format: `prefix`, `width`, `segment_mode`, `default_segment`, and `segment_map`. Projects created without this section fall back to `al` prefix, width 4, and `none` segment mode, preserving backward compatibility.

#### Record Type Registry

**Parent:** block-0041
**Interfaces:** RECORD_TYPES registry, CLI_KIND_ALIASES, RecordTypeSpec dataclass, MetadataFieldSpec dataclass, metadata_field_specs_for_record_type()
**Location:** archledger/record_types.py

`record_types.py` is the authoritative registry for arc42 record kinds. Each
`RecordTypeSpec` maps a kind to its directory, filename prefix, section,
template, aliases, default status and level, context factory, and typed metadata
fields.

`MetadataFieldSpec` describes supported value shapes and nullability. Shared
fields such as `applies_to`, `level`, and `parent` combine with per-type fields
for requirements, stakeholders, runtime scenarios, diagrams, interfaces, and
other records. The Model Layer consumes this contract during validation, while
CLI metadata mutation accepts explicit JSON, raw strings, or YAML/JSON files.

Diagram records default to text and support text, ascii, unicode, svgbob, and
mermaid content with type-specific scaffolding and checks.

#### Check Layer

**Parent:** block-0041
**Interfaces:** content_warnings()
**Location:** archledger/checks.py

The `checks.py` module provides per-record-type content validation beyond structural checks. The main entry point is `content_warnings()`, which returns a list of warning strings for a given `ArchitectureRecord`. It dispatches to type-specific checkers registered in `_CONTENT_WARNING_CHECKERS`: quality goals require scenarios, stakeholders require expectations, constraints require impact and valid categories, ADRs require Context/Decision/Consequences sections and deciders, quality scenarios require measurable response measures, risks require valid severity/probability and mitigation, and so on. It also detects placeholder text in record bodies and cross-dialect syntax contamination (e.g., AsciiDoc headings in Markdown records).

For diagram records, the check layer validates the `diagram_type` field against the allowed set (`text`, `ascii`, `unicode`, `svgbob`, `mermaid`), verifies that the body contains the appropriate fenced or literal block for the declared type and source dialect (Markdown uses ` ```textdiagram `/` ```svgbob `/` ```mermaid ` fences; AsciiDoc uses `[source,text]`+`----`, `[svgbob]`+`....`, or `[mermaid]`+`....` blocks), and checks for empty diagram blocks. Text-type diagrams (`text`, `ascii`, `unicode`) receive an additional line-length check (120 characters max) to keep diagrams readable in terminals and Git diffs.

This module was extracted from `repository.py` to isolate validation logic.

#### Source Ref Validation

**Parent:** block-0041
**Interfaces:** normalize_source_refs(), validate_relative_posix_path()
**Location:** archledger/source_refs.py

The `source_refs.py` module handles validation and normalization of source traceability links on architecture records. `validate_relative_posix_path()` enforces that source ref paths are relative, use POSIX separators, and do not traverse parent directories. `normalize_source_refs()` processes the raw `source_refs` list from YAML front matter, supporting both shorthand string syntax (`path/to/file.py#SymbolName`) and full mapping syntax with explicit path, symbols, and reason. It verifies that referenced paths and directories actually exist in the workspace. `RelativePosixPathError` provides structured error reporting for invalid paths. This module was extracted from `model.py` to keep source ref validation independent from the core data model.

#### ID Utilities

**Parent:** block-0041
**Interfaces:** LedgerIdFormat.format(), LedgerIdFormat.parse(), LedgerIdFormat.parse_parts(), LedgerIdFormat.is_id(), LedgerIdFormat.pattern(), LedgerIdFormat.reference_pattern(), format_ledger_id(), parse_ledger_id(), parse_ledger_id_parts(), is_ledger_id(), filename_for_ledger_id(), ledger_id_from_filename(), validate_id_prefix(), validate_id_width(), validate_id_segment_mode(), validate_id_segment()
**Location:** archledger/ids.py

The `ids` module provides centralized ledger ID handling with configurable prefix, width, and segment mode. The core abstraction is `LedgerIdFormat`, a frozen dataclass that encapsulates the three ID format parameters and exposes methods for formatting, parsing, pattern generation, and validation.

**Unsegmented mode** (`segment_mode=none`, default): IDs follow `<prefix>_<number>` (e.g., `al_0001`). `format(number)` produces the zero-padded string, `parse(id)` extracts the number, and `pattern()`/`reference_pattern()` produce regexes for exact matching and cross-reference detection respectively.

**Segmented mode** (`segment_mode=type`): IDs follow `<prefix>_<segment>_<number>` (e.g., `adr-0077`). `format(number, segment=...)` includes the validated segment token, and `parse_parts()` returns a `ParsedLedgerId` with both `number` and `segment` fields.

Module-level convenience functions (`format_ledger_id`, `parse_ledger_id`, `is_ledger_id`, etc.) accept optional `prefix`, `width`, and `segment_mode` parameters for callers that need ad-hoc format handling. Validators (`validate_id_prefix`, `validate_id_width`, `validate_id_segment_mode`, `validate_id_segment`) enforce format constraints shared across config parsing, CLI validation, and record checks.

The `LedgerIdFormat` instance is constructed from `ProjectConfig.id_format` and threaded through repository, renumber, and check operations as the single source of truth for ID syntax rules.

#### Renumber Service

**Parent:** block-0041
**Interfaces:** renumber_project()
**Location:** archledger/renumber.py

The `renumber` module provides the `renumber_project()` service that replans and optionally applies changes to the ledger ID format across all source files. It supports changing the ID prefix, width, and segment mode.

The renumber workflow operates in two phases: first it builds a rename plan (collecting numbered paths, computing new IDs via the configured `LedgerIdFormat` and segment resolution) and a rewrite plan (finding and replacing all ID references in source files). Then, if `apply=True`, it atomically rewrites file contents, renames files via a two-phase temp-file strategy to avoid collisions, updates `archledger.toml` with the new ID format settings, and recomputes `storage.yaml` counters.

When `apply=False` (dry-run, the default), it validates the plan and returns the computed changes without modifying any files. The CLI `renumber` command delegates to this service and formats the result for human or JSON output.

Key data structures: `RenumberResult` (top-level result with old/new format, renamed paths, rewritten files), `RenumberedPath` (old/new ID and path pair), and `RewrittenFile` (path with replacement count).

#### ID Segment Resolution

**Parent:** block-0041
**Interfaces:** id_segment_for_metadata(), id_segment_for_record(), id_segment_for_new_record()
**Location:** archledger/id_segments.py

The `id_segments` module resolves content-derived ID segments for segmented ledger IDs. When `segment_mode` is `type`, each record ID includes a segment token derived from the record's type metadata.

Resolution priority:

1. Explicit `id_segment` in the record's front matter metadata.
2. Mapped segment from the configured `segment_map` keyed by record `type`.
3. The configured `default_segment` as fallback.

Three entry points serve different callers: `id_segment_for_metadata()` for raw metadata dicts (used by renumber), `id_segment_for_record()` for loaded `ArchitectureRecord` objects (used by repository), and `id_segment_for_new_record()` for record creation where the kind is known but no record exists yet. All three validate the resolved segment against the `ID_SEGMENT_PATTERN` regex via `validate_id_segment()`.

This module is intentionally thin — it isolates the resolution policy so that `renumber.py` and `repository.py` share the same logic without coupling to each other.

#### Record Mutation Service

**Parent:** block-0041
**Interfaces:** export_record_document(), apply_record_document(), set_record_meta(), replace_record_body(), add_source_ref(), add_test_ref(), add_link(), add_acceptance_criterion()
**Location:** archledger/mutations.py, archledger/storage/frontmatter.py
**Fulfilled requirements:** content-0017

The Record Mutation Service provides the supported write path for existing
architecture records. It updates status, typed metadata, bodies, source and test
references, links, and inline acceptance criteria while preserving record
identity and incrementing the record version once per logical mutation.

`record export` emits a complete editable record document. `record apply`
validates the candidate identity and kind, ignores a caller-supplied version,
and increments from the stored version only when content changed. CLI mutation
commands snapshot the original text, run repository validation after the write,
and restore the original record if the target becomes invalid.

The service owns mutation mechanics only. Repository validation owns record and
cross-reference rules, while the CLI owns argument parsing, typed value input,
and human or JSON presentation.

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
**Consumers:** Check/read/build pipelines, Record Mutation Service, Migration flows
**Protocol:** YAML front matter + Markdown/AsciiDoc body
This interface defines canonical record files under `.archledger/records/` and
section files under the active profile. Each document contains YAML front matter
plus a Markdown or AsciiDoc body.

The contract includes stable record identity, kind and type, lifecycle status,
section and order, body format, and a monotonically increasing version. The
Record Type Registry adds per-type metadata shapes. Repository checks validate
identity, filenames, typed metadata, source and test references, and
cross-record links.

Storage parses and writes the document. The Record Mutation Service preserves ID
and kind, ignores externally supplied version changes, increments once for a
logical change, and supports rollback after failed validation.

# Runtime View

Key runtime scenarios cover project initialization, record creation, strict
validation, safe complete-record replacement with rollback, document assembly
and conversion, source snapshot and impact detection, focused context and trace
queries, source dialect conversion, and ledger ID renumbering.

See the [Build Pipeline Flow diagram](#diagram-al_diagram_0059) for the document
assembly path. The safe mutation scenario describes the supported edit and
apply path for existing records.

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

1. The CLI resolves project configuration and constructs the Repository.
2. Storage parses sections and live record files with their configured dialect.
3. Core validation checks required fields, lifecycle values, ID and filename
   consistency, segment expectations, and body format.
4. The Model obtains per-record metadata field specifications from the Record
   Type Registry and validates scalar, list, and object shapes.
5. Repository checks duplicate IDs, parents, links, source and test references,
   and archive invariants.
6. Specialized checks report placeholders and type-specific completeness issues.
7. Normal mode fails on errors. Strict mode also promotes warnings to a failing
   result.
8. The CLI emits the same result through human formatting or a JSON envelope.

## Initialize a new project

1. CLI checks that `archledger.toml` does not already exist.
2. CLI collects init options for all configuration domains: build defaults (`--build-default-format`, `--build-default-output`, `--build-converter`, etc.), diagrams (`--diagrams`, `--diagram-renderer`, `--diagram-default-type`), arc42 metadata (`--arc42-title`, `--arc42-language`, `--arc42-template-version`), source tracking (`--tracking/--no-tracking`, `--tracking-scanner`, `--tracking-include`, `--tracking-exclude`), and ID format (`--id-prefix`, `--id-width`, `--id-segment-mode`). Each option maps directly to a field in `archledger.toml`.
3. CLI calls `build_default_project_config()` to construct a validated `ProjectConfig` dataclass, then renders it to TOML via `render_project_config()`.
4. CLI writes the config file and resolves project paths.
5. Repository creates the archledger_dir, sections_dir, records_dir, and build_dir.
6. Repository creates one subdirectory for each unique record type directory from `RECORD_TYPE_TO_DIR` (currently 16 directories).
7. Repository writes 12 section files named with the configured ledger ID format and section extension, for example `al_0001.adoc` in unsegmented AsciiDoc projects or `content-0001.md` in segmented Markdown projects.
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

## Safely replace an architecture record

1. The user invokes `archledger record export RECORD_ID --output FILE`.
2. The CLI resolves the record and the mutation service verifies its identity
   before exporting the complete front-matter document.
3. The user edits metadata and body content in the exported file.
4. The user invokes `archledger record apply RECORD_ID --from-file FILE`.
5. The mutation service parses the candidate, verifies that ID and kind match
   the stored record, and compares normalized metadata and body content.
6. If unchanged, the command reports no change and preserves the version.
7. If changed, the service writes the candidate with exactly one version
   increment, regardless of the version supplied in the candidate.
8. The Repository checks the resulting target record and relevant contracts.
9. On validation failure, the CLI atomically restores the original text and
   returns an error. Otherwise it reports the applied change.

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

Cross-cutting concepts include record lifecycle and archival, project config and
path discovery, dual-source dialect rendering, typed metadata contracts,
versioned mutation with rollback, record and link identity, multi-type diagram
validation, and source tracking with impact analysis. Focused context and trace
queries make those contracts consumable by coding agents without expanding
Archledger into a behavior-specification or workflow orchestrator.

The [Source Tracking Flow diagram](#diagram-al_diagram_0076) visualizes baseline
comparison and record impact resolution.

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

Every live record has a status: `draft`, `proposed`, `accepted`, `deprecated`, or
`superseded`. Status controls default visibility in reads and builds. Draft and
incomplete live records produce validation findings; explicit include options
can expose hidden lifecycle states.

Archiving is separate from status. `archledger archive` moves an obsolete record
to the archive, preserves its ledger number, and leaves a tombstone so identity
is never reused. Archived records are historical evidence and are not mutated to
silence live-content warnings.

All supported live-record mutations increment the version once when content
changes. No-op complete-document apply preserves the version, and failed target
validation restores the original text.

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

Format: `<prefix>_<segment>_<number>` (e.g., `adr-0077`, `block-0042`). The segment is derived from the record's `type` field via the configured `segment_map`, with an explicit `id_segment` override in front matter, falling back to `default_segment`.

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

**Document version:** 2

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

**Document version:** 2

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

**Document version:** 2

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

**Document version:** 2

## Context

Source-state tracking needs strong change detection and compact persisted metadata.

## Decision

Persist per-file SHA-256 hashes only, plus derived directory hashes and counts in source state snapshots.

## Consequences

Improves determinism and avoids unstable file-size/mtime dependence; requires content hashing during scan.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Config v7 and source schema v2 are the release baseline

**Document version:** 2

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

**Document version:** 2

## Context

Core build workflows should be available in clean Python environments without external binaries.

## Decision

Require no external converter tools for native Markdown/AsciiDoc outputs.

## Consequences

Improves portability; non-native formats remain optional.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Non-native exports delegate to pandoc or asciidoctor

**Document version:** 2

## Context

Supporting many export formats inside Python would duplicate mature tooling and increase maintenance burden.

## Decision

Delegate non-native conversions to pandoc/asciidoctor family tools.

## Consequences

Clear dependency errors are required when tools are missing.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Output path resolution remains bounded to configured roots

**Document version:** 2

## Context

Architecture output generation must not permit accidental writes outside intended roots.

## Decision

Keep output path resolution bounded by configuration/workspace validation rules.

## Consequences

Safer defaults; invalid paths fail early with explicit diagnostics.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Source refs use relative POSIX paths without parent traversal

**Document version:** 2

## Context

Source references must safely link docs to code while preventing ambiguous or unsafe paths.

## Decision

Require relative POSIX source_refs that do not traverse parent directories.

## Consequences

Traceability links stay portable and secure; invalid refs are rejected.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Storage counters are metadata and can be recomputed

**Document version:** 2

## Context

Stored counters optimize metadata reads but can drift after manual edits or transfers.

## Decision

Treat storage counters as recomputable metadata, not canonical truth.

## Consequences

Repair/recount operations can restore consistency without data loss.

## Alternatives considered

- Keep legacy behavior unchanged: rejected because it leaves release-critical ambiguity.

## Multi-type diagram support with text as default

**Document version:** 2

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

**Document version:** 2

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

**Document version:** 2

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

**Document version:** 2

## Context

In projects with many records (50+), flat `al_NNNN` numbering makes it hard to identify a record's type from its ID alone. Scanning `al_0042` gives no hint whether it is an ADR, building block, or runtime scenario. This hurts navigation in large ledgers and in cross-references between records.

## Decision

When `segment_mode=type`, ledger IDs include a type-derived segment token: `<prefix>_<segment>_<number>` (e.g., `adr-0077`, `block-0042`). The segment is resolved deterministically from the record's `type` metadata via the configured `segment_map`, with an explicit `id_segment` front-matter field as an override, and `default_segment` as fallback.

Segment tokens are validated against `^[a-z][a-z0-9-]{1,31}$`. The default segment map maps each record type to a short token (e.g., `adr` → `adr`, `white_box` → `block`, `runtime_scenario` → `runtime`).

The global numeric sequence is preserved: numbering remains sequential across all types regardless of segment. Renumber can toggle segment mode on or off while keeping numbers stable.

## Consequences

- IDs become self-describing: `adr-0077` is clearly an architecture decision.
- File names sort predictably within type directories (e.g., `.archledger/records/decisions/adr-0077.md`).
- Cross-references in record bodies update correctly during renumber.
- The `none` segment mode preserves backward compatibility for projects that prefer flat numbering.

## Alternatives considered

- Per-type counters: rejected because it would break the single global sequence invariant and complicate renumbering.
- Opaque hash segments: rejected because they would not be human-readable.

# Quality Requirements

The top quality scenarios address deterministic builds and agent-friendly CLI interaction. These directly support the quality goals of reproducibility, maintainability, and traceability.

## Quality Requirements Overview

| Title                                      | Category      | Measure                                                                         | Scenarios                  |
| ------------------------------------------ | ------------- | ------------------------------------------------------------------------------- | -------------------------- |
| Deterministic native build output          | reliability   | Byte-identical output for equal accepted records and deterministic date source. | quality-0093, quality-0101 |
| Fast check and build on small repositories | performance   | check/build complete in under 5s on representative small repositories.          | quality-0101               |
| Safe path validation                       | safety        | Path escape attempts are rejected with explicit errors.                         | quality-0099               |
| Clear converter failure diagnostics        | operability   | Converter failures identify missing tool and installation hint.                 | quality-0095               |
| JSON output stability                      | compatibility | JSON payload keys for stable commands remain backward compatible.               | quality-0100               |
| Source tracking correctness                | correctness   | Source tracking reports file and impact deltas accurately.                      | quality-0097               |

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
