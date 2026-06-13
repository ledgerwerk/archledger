---
id: context-0036
type: context_interface
title: Coding agent harness
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: context_and_scope
order: 20
context_kind: technical
partner: Coding Agent
inputs:
  - CLI invocations (archledger init, new, check, build, read, show, source snapshot,
    source changed, source convert, etc.)
  - JSON --json flag for structured output
outputs:
  - JSON payloads (ok, command, result, warnings)
  - Human-readable CLI output
channels:
  - Process stdout/stderr
  - Exit codes (0 success, 1 failure)
source_refs:
  - archledger/section_rendering.py
  - tests/test_build.py
kind: context
---

Coding agents (pi, opencode, etc.) invoke archledger through its CLI, passing `--json` for machine-readable output. The agent skill file (`SKILL.md`) provides the protocol for how agents should interact with archledger: locate config, inspect records via `read`, detect changes via `source changed`, create/update in batches via `new`, validate with `check`, render with `build`, and persist baselines with `source snapshot`.
