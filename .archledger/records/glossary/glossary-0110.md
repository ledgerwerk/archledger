---
id: glossary-0110
type: glossary_term
title: Source Ref
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: glossary
order: 60
term: Source Ref
definition:
  A traceability link from an architecture record to a source code artifact.
  Source refs have a path (relative to workspace root), optional symbols, and an optional
  reason. They enable change impact analysis.
source_refs:
  - README.md
  - docs/agent-workflow.rst
kind: glossary
---

A traceability link from an architecture record to a source code artifact. Source refs have a path (relative to workspace root), optional symbols (e.g., class or function names), and an optional reason. Directory refs end with `/`. The `changed` command cross-references source refs against changed files to identify impacted records.
