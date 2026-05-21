---
id: black_box_0001
type: black_box
title: "CLI Layer"
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 10
interfaces:
  - archledger console script (stdin/stdout)
location:
  - archledger/cli.py
  - archledger/launcher.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T05:52:14Z"
updated_at: "2026-05-20T12:00:00Z"
---

The Typer-based CLI exposes commands: `init`, `status`, `where`, `new`, `seed`, `list`, `show`, `read`, `check`, `build`, `snapshot`, `changed`, `convert-sources`. Each command resolves the project config, constructs a Repository, and delegates to it. Two output modes are supported: human-readable text (default) and structured JSON (`--json` flag). Error handling maps domain exceptions (`ArchledgerError` subclasses) to appropriate exit codes and error output.

The `snapshot` and `changed` commands integrate the source tracking subsystem. The `convert-sources` command delegates to the migration module for Markdown-to-AsciiDoc source conversion.
