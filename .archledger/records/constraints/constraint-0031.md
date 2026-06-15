---
id: constraint-0031
type: constraint
title: No GUI or web interface
schema_version: 4
body_format: markdown
status: accepted
section: architecture_constraints
order: 30
category: technical
impact:
  All interaction is through the command line. The --json flag is the machine
  interface for agents.
source_refs:
  - pyproject.toml
  - archledger/storage/paths.py
  - tests/test_paths.py
kind: constraint
version: 1
---

archledger exposes no GUI or web interface. All user interaction happens through the Typer CLI. This simplifies the architecture and makes automation straightforward, but means users must be comfortable with command-line tools.
