---
schema_version: 4
id: content-0027
type: requirement
title: CLI provides stable machine-readable JSON output
status: accepted
section: introduction_and_goals
order: 90
source: archledger CLI behavior and repository implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_read_cli.py
  - path: archledger/cli_payloads.py
    role: implements
    reason: Shapes stable command-specific JSON payloads.
acceptance_criteria:
  - id: AC-001
    statement:
      JSON-mode success and handled-error responses remain parseable objects
      with stable ok, command, result or error fields.
    validation:
      command: pytest -q tests/test_read_cli.py tests/test_repository_cli.py
      expected: passes
test_refs:
  - tests/test_read_cli.py
  - tests/test_repository_cli.py
kind: content
version: 1
---

## Requirement

CLI commands supporting `--json` must provide stable machine-readable payloads suitable for automation.

## Rationale

Agents and CI pipelines depend on predictable command contracts.
