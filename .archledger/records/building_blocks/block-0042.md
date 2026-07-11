---
id: block-0042
type: black_box
title: CLI Layer
schema_version: 4
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
source_refs:
  - archledger/cli.py
  - archledger/cli_formatting.py
  - archledger/cli_payloads.py
  - archledger/launcher.py
  - docs/cli.md
  - path: skills/archledger/SKILL.md
    reason: External skill documentation updated for renumber and ID format commands
kind: block
version: 3
---

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
