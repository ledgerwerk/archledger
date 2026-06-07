---
schema_version: 2
id: al_content_0138
type: requirement
title: "BDD metadata imports and exports supported Gherkin scenarios"
status: proposed
section: introduction_and_goals
order: 130
date: "2026-06-07"
source: BDD metadata import and export implementation
priority: must
stakeholders: []
quality_goals: []
body_format: markdown
created_at: "2026-06-07T09:11:15Z"
updated_at: "2026-06-07T09:11:15Z"
source_refs:
  - path: archledger/bdd/
    role: implements
    reason: Parses, normalizes, imports, and exports supported Gherkin behavior.
  - path: archledger/sdd.py
    role: validates
    reason: Applies SDD policy to accepted records carrying BDD metadata.
test_refs:
  - tests/test_bdd_import_cli.py
  - tests/test_bdd_export_cli.py
  - tests/test_bdd_checks.py
acceptance_criteria:
  - id: AC-001
    statement: Supported Gherkin features import as behavior records with normalized BDD metadata and export back to a feature file without executing automation commands.
    validation:
      command: pytest -q tests/test_bdd_import_cli.py tests/test_bdd_export_cli.py tests/test_bdd_checks.py
      expected: passes
---

## Requirement

Archledger must import the supported Gherkin subset into runtime or quality
scenario records and export records with valid `bdd` metadata as feature files.
Automation metadata is stored only for traceability; Archledger never invokes a
BDD runner.

## Rationale

Behavior examples remain part of the canonical architecture ledger while teams
can exchange Gherkin artifacts with existing discovery and test workflows.
