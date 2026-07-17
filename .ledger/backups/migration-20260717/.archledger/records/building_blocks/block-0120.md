---
schema_version: 4
id: block-0120
type: interface
title: CLI stdout JSON contract
status: accepted
section: building_block_view
parent: null
order: 10
providers:
  - CLI Layer
consumers:
  - Automation scripts
  - JSON-mode CLI users
protocol: JSON over stdout
body_format: markdown
source_refs:
  - archledger/cli_payloads.py
  - archledger/cli_formatting.py
  - archledger/cli.py
  - tests/test_read_cli.py
kind: block
version: 1
---

This interface defines the stable stdout contract for CLI commands when users opt into `--json` mode.

- **Provider**: CLI Layer (`archledger/cli.py`) with payload shaping in `archledger/cli_payloads.py`.
- **Consumers**: automation scripts, coding-agent loops, CI checks, and tests that parse JSON output.
- **Protocol**: JSON object payloads emitted to stdout on success and JSON error payloads on handled failures.

The contract guarantees machine-readable top-level fields (`ok`, `command`, and command-specific result payloads) so tooling can branch on command outcomes without scraping human text output.
