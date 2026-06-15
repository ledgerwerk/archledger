---
id: constraint-0029
type: constraint
title: Typer CLI interface
schema_version: 4
body_format: markdown
status: accepted
section: architecture_constraints
order: 10
category: technical
impact:
  All user-facing functionality is exposed through Typer CLI commands. No GUI,
  no web API, no library-first API.
source_refs:
  - pyproject.toml
  - archledger/storage/paths.py
  - tests/test_paths.py
kind: constraint
version: 1
---

archledger uses Typer as its CLI framework. The entry point is `archledger.launcher:main`, registered as the `archledger` console script. All commands return either human-readable text or `--json` structured output. This constraint keeps the tool focused on CLI and automation workflows.
