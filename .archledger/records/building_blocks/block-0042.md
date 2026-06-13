---
id: block-0042
type: black_box
title: CLI Layer
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: block-0041
order: 10
interfaces:
  - archledger console script (stdin/stdout)
location:
  - archledger/cli.py
  - archledger/cli_formatting.py
  - archledger/cli_payloads.py
  - archledger/launcher.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T05:52:14Z"
updated_at: "2026-05-23T11:30:00Z"
source_refs:
  - archledger/cli.py
  - archledger/cli_formatting.py
  - archledger/cli_payloads.py
  - archledger/launcher.py
  - docs/cli.rst
  - path: skills/archledger/SKILL.md
    reason: External skill documentation updated for renumber and ID format commands
kind: block
---

The Typer-based CLI exposes top-level commands: `init`, `status`, `paths`, `schema`, `new`, `seed`, `list`, `show`, `read`, `check`, `archive`, `doctor`, `renumber`, `build`, and the `source` subgroup. The `source` subgroup contains `snapshot`, `changed`, and `convert` for source tracking and dialect migration. `archive` preserves obsolete records without reusing ledger numbers, and `doctor` validates or repairs ledger numbering invariants. Each command resolves the project config, constructs a Repository, and delegates to it. Two output modes are supported: human-readable text (default) and structured JSON (`--json` flag). Error handling maps domain exceptions (`ArchledgerError` subclasses) to appropriate exit codes and error output.

Output is split across three modules: `cli.py` defines Typer commands and dispatches to the Repository, `cli_payloads.py` constructs structured JSON dictionaries from domain result types, and `cli_formatting.py` renders human-readable messages from those payloads. This separation keeps the command definitions thin and testable.

The `init` command accepts comprehensive CLI options covering all configuration domains: build defaults (`--build-default-format`, `--build-converter`, `--build-pdf-engine`, etc.), diagrams (`--diagrams`, `--diagram-renderer`, `--diagram-default-type`), arc42 metadata (`--arc42-title`, `--arc42-language`, `--arc42-template-version`), source tracking (`--tracking/--no-tracking`, `--tracking-scanner`, `--tracking-include`, `--tracking-exclude`), and ID format (`--id-prefix`, `--id-width`, `--id-segment-mode`). Options are validated against shared constants from `config/model.py` before config generation.

The `renumber` command delegates to the Renumber Service (`renumber.py`) to replan and optionally apply ID format changes. It is dry-run by default; `--apply` is required to execute mutations. It accepts `--id-prefix`, `--id-width`, and `--id-segment-mode` to specify the target format.

The `source snapshot` and `source changed` commands integrate the source tracking subsystem. The `source convert` command delegates to the migration module for Markdown-to-AsciiDoc source conversion.
