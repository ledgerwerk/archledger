---
id: runtime-0060
type: runtime_scenario
title: Initialize a new project
schema_version: 4
body_format: markdown
status: accepted
section: runtime_view
order: 30
participants:
  - CLI Layer
  - Repository Layer
  - Storage Layer
trigger: User invokes `archledger init` in a project directory
result:
  Config file created with full init options (build, diagrams, arc42, tracking),
  directory scaffold initialized with 12 section files and 16 record subdirectories.
source_refs:
  - archledger/cli.py
  - archledger/config/render.py
  - tests/test_init_cli.py
kind: runtime
version: 1
---

1. CLI checks that `archledger.toml` does not already exist.
2. CLI collects init options for all configuration domains: build defaults (`--build-default-format`, `--build-default-output`, `--build-converter`, etc.), diagrams (`--diagrams`, `--diagram-renderer`, `--diagram-default-type`), arc42 metadata (`--arc42-title`, `--arc42-language`, `--arc42-template-version`), source tracking (`--tracking/--no-tracking`, `--tracking-scanner`, `--tracking-include`, `--tracking-exclude`), and ID format (`--id-prefix`, `--id-width`, `--id-segment-mode`). Each option maps directly to a field in `archledger.toml`.
3. CLI calls `build_default_project_config()` to construct a validated `ProjectConfig` dataclass, then renders it to TOML via `render_project_config()`.
4. CLI writes the config file and resolves project paths.
5. Repository creates the archledger_dir, sections_dir, records_dir, and build_dir.
6. Repository creates one subdirectory for each unique record type directory from `RECORD_TYPE_TO_DIR` (currently 16 directories).
7. Repository writes 12 section files named with the configured ledger ID format and section extension, for example `al_0001.adoc` in unsegmented AsciiDoc projects or `content-0001.md` in segmented Markdown projects.
8. Repository writes the storage.yaml metadata file.
9. The project is ready for `archledger new` commands. Record creation will use the configured ID format (prefix, width, segment mode).
