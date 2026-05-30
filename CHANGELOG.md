# Changelog

All notable changes to `archledger` will be documented in this file.

## Unreleased

_(No unreleased changes.)_

## 0.2.0 — 2026-05-30

Configurable ID formats, content-segmented ledger IDs, `archledger renumber` command, comprehensive `init` CLI options, Markdown as the default source format, and a major internal refactoring across 5 phases.

### Added

- **Configurable ledger ID format** — `archledger.toml` `[ids]` table with `id_prefix` and `id_width` settings (config v6); `archledger init --id-prefix`/`--id-width` options set the format at project creation (task-0019).
- **Content-segmented ledger IDs** — `segment_mode`, `default_segment`, and `segment_map` in config v7 enable arc42-chapter-prefixed record IDs (e.g. `al_introduction_0001`); `init --id-segment-mode` and `renumber --id-segment-mode` options (task-0020).
- **`archledger renumber` command** — dry-run by default, `--apply` to rewrite record IDs and update cross-references; supports prefix/width changes and segment-mode transitions with collision detection and two-phase renames (task-0019, task-0020).
- **Comprehensive `init` CLI options** — `--diagrams`/`--no-diagrams`, `--diagram-renderer`, `--diagram-default-type`, `--build-default-output`, `--build-default-output-dir`, `--arc42-*`, `--tracking`/`--no-tracking`, `--tracking-*`, `--project-uuid`, and `--id-prefix`/`--id-width`/`--id-segment-mode` (task-0018, task-0019, task-0020).
- **Interface records** — accepted architecture records documenting the CLI JSON stdout contract and front-matter record file contract (task-0021).

### Changed

- **Markdown as default source format** — `archledger init` now creates Markdown projects by default instead of AsciiDoc (task-0023).
- **Config version v6 → v7** — `[ids]` table added in v6, content-segment fields added in v7; migration floor raised to v7 (task-0019, task-0020).
- **ID-config-aware internals** — repository, validation, counter recomputation, and renumber modules are fully parameterized on configured ID prefix, width, and segment mode (task-0019, task-0020).
- **Architecture docs remediation** — updated building-block, runtime, glossary, and quality-scenario records; corrected source-tracking policy to exclude `_version.py`; regenerated ARCHITECTURE.md (task-0021).
- **Skill default** — `skill.installed` now defaults to `false` in generated `archledger.toml` (task-0018).
- **Internal refactoring (5 phases)** — deduplicated helpers (`known_source_extensions`, `is_relative_to`, `SourceFormatSpec`, `_validate_uuid`) centralized in model/storage; CLI boilerplate reduced with payload helpers, `_run_simple_command`, and `InitOptions` dataclass; config schema consolidated with `config/schema.py` data-driven `FieldSpec`/`TableSpec`; diagram/template handling unified with shared `_materialize_blocks` and `DiagramSyntax` registry; repository split into facade + `record_store.py` + `repository_checks.py` + `ledger_sequence.py` + `doctor.py` + `archive.py` (task-0022).

### Fixed

- `archledger init` crash when `enabled` kwarg was passed to the tracking table parser (task-0023).
- README PyPI URL and unsupported kroki renderer claim corrected (task-0021).
- Build/output path guidance in docs aligned with current config-driven behavior (task-0021).

## 0.1.0 — 2026-05-22

First public release of archledger — a source-first arc42 architecture documentation tool backed by Markdown or AsciiDoc records, YAML front matter, validation, drift tracking, and optional exports.

### Added

- **AsciiDoc & Markdown dual-source model** — choose AsciiDoc (default) or Markdown source fragments with a shared assembly pipeline (task-0003, task-0005).
- **Multi-format build & export** — build to HTML, PDF, DOCX, Markdown, RST, Textile via Pandoc/Asciidoctor with a DocBook intermediate for RST output (task-0003, task-0004, task-0005).
- **Source migration CLI** — `archledger source convert --apply` migrates Markdown sources to AsciiDoc with Pandoc (task-0003, task-0008).
- **Config v5** — `source.schema_version`, `tracking`, `build.default_output`, `diagrams`, and per-output DOCX reference-document overrides (task-0005, task-0008, task-0013, task-0014).
- **Workspace source-state tracking** — `archledger snapshot` / `archledger changed` commands with SHA-256-only v2 state and derived directory hashes (task-0006, task-0011).
- **Deterministic build date** — `SOURCE_DATE_EPOCH` or record metadata–derived document date for reproducible builds (task-0013).
- **Diagram records** — first-class text-diagram support (default `text`), plus optional Mermaid materialization via `mmdc`; supported types: `text`, `ascii`, `unicode`, `svgbob`, `mermaid` (task-0014, task-0015).
- **Unified ledger-wide `al_NNNN` IDs** — single global counter for sections (`al_0001`–`al_0012`) and records (`al_0013`+) replacing legacy type-prefixed IDs; `check --strict` rejects legacy IDs (task-0016).
- **Archive & doctor workflow** — `archledger archive` moves records to `.archledger/archive/`; `archledger doctor` repairs counter gaps and corruption; removed `check --fix` in favor of read-only check + doctor (task-0017).
- **Record-type registry** — centralized `archledger/record_types.py` with registry-backed template factories for all record kinds (task-0010).
- **Config module split** — dedicated `archledger/config/` package with `model.py`, `parse.py`, `render.py` and backward-compatible re-exports (task-0010).
- **Atomic file writes** — canonical sources, storage metadata, and source-state snapshots are written atomically via temp-file + rename (task-0010).
- **Custom record extension support** — configured `record_extension` is honoured during counter recomputation; overwrite guard prevents stale-counter file replacement (task-0007).
- **GitHub Actions CI** — Python 3.10–3.13 quality matrix, package build, wheel smoke checks, and optional converter integration job (task-0009).
- **Converter integration tests** — gated real-tool tests for Pandoc and Asciidoctor-backed builds (task-0009).
- **Sphinx documentation** — CLI guide, configuration reference, source model, source tracking, build/export, agent workflow, API reference, and release-process docs (task-0008, task-0009, task-0013).
- **`archledger --json schema`** — machine-readable schema payload with `id_strategy`, `id_pattern`, and `reserved_section_ids` (task-0016).
- **`archledger paths`** — JSON payload exposing `source_state_path` and other project paths (task-0012).
- **Dogfooded architecture** — 10 requirements, 6 quality requirements, deployment records, release-critical ADRs, quality scenarios, system/build diagrams, and full `source_refs` traceability (91/91 records) in the self-hosted `.archledger/` (task-0013).

### Changed

- **CLI surface cleanup** — renamed flags/arguments (`read --body`, `all-statuses`, `check --fix` → doctor, `build --format` repeatable, `source convert --apply`); old top-level commands reorganized under `paths`, `schema`, `source` groups (task-0012).
- **Build output resolution** — `build.default_output_dir` is resolved from the workspace root instead of `.archledger/` (task-0011).
- **Source-state format** — v2 SHA-only payloads replace size/mtime fields; directory hashes are derived (task-0011).
- **Packaging** — `pyproject.toml`–only builds; legacy `setup.py` removed; raised setuptools/setuptools-scm requirements (task-0009).
- **Config validation** — boolean values for `config_version`, `storage.yaml` counters, and `source.schema_version` are now rejected (task-0009).
- **Section rendering** — empty fulfilled-requirements and risks labels are hidden in assembled output (task-0013).
- **Pandoc export path** — RST and other Pandoc-backed exports route through an Asciidoctor → DocBook intermediate instead of direct AsciiDoc input (task-0004).

### Fixed

- `config_version = true` is rejected instead of being accepted as integer `1` (task-0009).
- `storage.yaml` boolean counters (e.g. `next_numbers.requirement: true`) are rejected (task-0009).
- Source-ref and source-state path validation consistently enforce POSIX-relative path rules (task-0009).
- Custom record extension no longer causes counter overwrite on repeated creation (task-0007).
- CLI `snapshot`/`changed` blocked when tracking is disabled (task-0008).
- Directory `source_refs` validated during record loading (task-0008).
- Source migration preserves modern config fields through v5 (task-0008).
