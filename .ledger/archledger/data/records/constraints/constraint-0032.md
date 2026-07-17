---
id: constraint-0032
type: constraint
title: Python 3.10+ runtime
schema_version: 4
body_format: markdown
status: accepted
section: architecture_constraints
order: 40
category: technical
impact:
  All user-facing functionality is exposed through Typer CLI commands. No GUI,
  no web API.
source_refs:
  - pyproject.toml
  - archledger/storage/paths.py
  - tests/test_paths.py
kind: constraint
version: 1
---

archledger requires Python >= 3.10, as declared in `pyproject.toml`. This allows the use of modern type hint syntax (`X | Y` unions, `match` statements) while still supporting current Python distributions on Linux and macOS.
