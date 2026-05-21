---
id: runtime_0003
type: runtime_scenario
title: "Initialize a new project"
status: accepted
section: runtime_view
order: 30
participants:
  - CLI Layer
  - Repository Layer
  - Storage Layer
trigger: "User invokes `archledger init` in a project directory"
result: "Config file created, directory scaffold initialized with 12 section files and 15 record subdirectories."
---

1. CLI checks that `archledger.toml` does not already exist.
2. CLI renders the default TOML config with a generated project UUID, name derived from the directory, and source format from the `--source-format` option (defaults to `asciidoc`).
3. CLI writes the config file and resolves project paths.
4. Repository creates the archledger_dir, sections_dir, records_dir, and build_dir.
5. Repository creates 15 record subdirectories (one per record type directory).
6. Repository writes 12 section Markdown files (01_introduction_and_goals through 12_glossary) with section extensions matching the configured source format.
7. Repository writes the storage.yaml metadata file.
8. The project is ready for `archledger new` commands.
