---
id: al_runtime_0060
type: runtime_scenario
title: Initialize a new project
schema_version: 2
date: "2026-05-22"
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
  directory scaffold initialized with 12 section files and 15 record subdirectories.
source_refs:
  - archledger/cli.py
  - archledger/config/render.py
  - tests/test_init_cli.py
---

1. CLI checks that `archledger.toml` does not already exist.
2. CLI collects init options for all configuration domains: build defaults (`--build-default-format`, `--build-default-output`, `--build-converter`, etc.), diagrams (`--diagrams`, `--diagram-renderer`, `--diagram-default-type`), arc42 metadata (`--arc42-title`, `--arc42-language`, `--arc42-template-version`), and source tracking (`--tracking/--no-tracking`, `--tracking-scanner`, `--tracking-include`, `--tracking-exclude`). Each option maps directly to a field in `archledger.toml`.
3. CLI calls `build_default_project_config()` to construct a validated `ProjectConfig` dataclass, then renders it to TOML via `render_project_config()`.
4. CLI writes the config file and resolves project paths.
5. Repository creates the archledger_dir, sections_dir, records_dir, and build_dir.
6. Repository creates 15 record subdirectories (one per record type directory).
7. Repository writes 12 section Markdown files (01_introduction_and_goals through 12_glossary) with section extensions matching the configured source format.
8. Repository writes the storage.yaml metadata file.
9. The project is ready for `archledger new` commands.
