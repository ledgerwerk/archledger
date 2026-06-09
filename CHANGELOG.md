# Changelog

All notable changes to `archledger` will be documented in this file.

## Unreleased

_(No unreleased changes.)_

## 0.3.0 — 2026-06-09

SDD contract and profile upgrade, BDD/Gherkin metadata and tooling (import, export, validate, sync), scope metadata and monorepo support, combo trace, ID format drift repair, and release-hardening fixes.

### Added

- **SDD contract and profile upgrade** (task-0026) — SDD profile with enforceable traceability policy (`require_acceptance_criteria`, `require_implementation_refs`, `require_test_refs`), effective config policy merging, `sdd check`/`check-pr`/`status` CLI commands, profile gate, link-target-status warning, expanded JSON schemas (`sdd.v1`, `sdd-status.v1`, `sdd-pr.v1`), and `init --profile sdd`.
- **SDD review fixes** (task-0027) — hardened inline acceptance-criteria handling, normalized source/test reference checks, real PR gate for `check-pr`, `--include-drafts`/`--include-superseded`/`--all-statuses` flags, `sdd_options_from_config` merging config+CLI overrides, AC ergonomics (`--requirement`/`--validation-command`/`--validation-expected`), and `SddContext` refactored module.
- **BDD/Gherkin metadata and tooling** (task-0028) — BDD front-matter model (`BddAutomation`/`BddExample`), `normalize_bdd_metadata`, SDD-BDD checks (shape, GWT, automation, feature-ref, AC-link), minimal Gherkin parser, `bdd import`/`export` CLI, config flags (`require_bdd_gwt_for_behavior_records`, `require_bdd_automation_for_accepted_records`), JSON schemas (`bdd-import.v1`, `bdd-export.v1`), and docs/skill updates. Phases 0-5.
- **SDD/BDD review fixes** (task-0029) — P0 Gherkin parser fixes (removed `matched_scenario`, fixed `UnsupportedGherkinError`, fixed step bucket sharing), P1 profile UX (`bdd` is not a standalone profile, config preservation on enable/disable), P2 docs/stale-reference cleanup.
- **SDD/BDD integration review fixes** (task-0032) — safe/atomic/multi-rule batch export with path sanitization, JSON error envelopes for `bdd validate`/`sync`/`export` misuse, normalized export payloads, Option A linked/automated semantics, `behavior_linked` coverage dimension, GWT for `quality_scenario`, `sdd coverage --by-record`, `sdd-check.v2` schema, and new `bdd-sync`/`sdd-init`/`sdd-explain` schemas.
- **BDD/spec workflow alignment** (task-0033) — SpecWeave-owned `specs/behavior/features` convention, separate `source_refs` (feature files) from `test_refs` (pytest), deprecated path warnings across import/export/validate/sync, `bdd link` test_refs support, SDD BDD test-ref and path-convention rules.
- **Scope metadata and monorepo support** (task-0034) — `RecordScope` dataclass with `kind`/`name`/`applies_to`/`excludes`/`lifecycle`, scope normalization and context matching, `applies_to` link rel, `--scope`/`--scope-kind`/`--addon` CLI filters, `scope list`/`show`/`affected` subcommands, relaxed source-ref existence for archived records.
- **Combo trace** (task-0037) — `archledger trace --format combo-json` emitting `combi.trace.v1` bundles with source/test refs, BDD IDs, AC IDs, and Taskledger provenance; SDD external reference checks for Taskledger ID shapes and linked BDD automation; three-tool boundary documentation.
- **P0-P2 release hardening** (task-0038) — shared BDD mutation validation helpers, safe `bdd set`/`link` pre-validation, tightened Gherkin parser, cached feature-file parsing in sync, structured sync findings, extracted `sdd_support.py`/`sdd_indexes.py` modules, `sdd-check.v2` schema aliasing, markdown coverage formatting, JSON envelopes for early SDD validation errors, dedicated `docs/sdd.rst` and `docs/bdd-gherkin.rst` guide pages.

### Changed

- **Config version v7 → v8** — profile layout (`[profiles]`/`[profiles.arc42]`/`[profiles.sdd]`) introduced via `archledger profile migrate` (task-0028).
- **SDD linked-automation policy** — linked imports accepted by default; warns in `--strict`; errors only when `require_bdd_automation_for_accepted_records` is enabled (task-0032, task-0038).
- **BDD export payload** — normalized to `{schema, exported[], feature_files[], warnings[]}` for both single and batch (task-0032, task-0038).
- **`sdd check` payload** — migrated to `archledger.sdd-check.v2` with `default_profile`/`enabled_profiles`/`sdd_enabled` (task-0032).

### Fixed

- Test failures from markdown default source format change (task-0024).
- Archive tombstones rejected by check/build; added `archive_tombstone` to valid record types (task-0030).
- ID format drift: `doctor --repair` now refuses when ID format mismatches config; `renumber` supports `--from-prefix`/`--from-width`/`--from-id-segment-mode` for explicit migration; stale generated tombstone collision detection and quarantine (task-0035).
- Hidden config init guard: `init` checks both `archledger.toml` and `.archledger.toml`; renumber infers old segment mode from drift (task-0036).
- Profile enable/disable preserves existing profile settings instead of overwriting (task-0029).
- `scan_git_revision` skips `.archledger/build` state files, fixing spurious unlinked changes in PR checks (task-0027).
- `assert result.stderr` test failures migrated to `result.output` for combined-stream CliRunner (task-0028).

### Internal

- Code smell review: removed unused `repository_checks` module, unreachable model code, fixed `Callable` typing, added missing test annotations, aligned release docs with mypy scope (task-0025).

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
