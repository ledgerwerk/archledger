---
id: glossary-0111
type: glossary_term
title: Source State
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: glossary
order: 70
term: Source State
definition:
  A persisted source-tracking baseline with SHA-256 content hashes for tracked
  files plus derived directory hashes. Used by `archledger source changed` to detect
  modified, added, deleted, and possibly renamed files.
source_refs:
  - README.md
  - docs/agent-workflow.rst
kind: glossary
---

A source state is the JSON baseline written by `archledger source snapshot`. It is stored at `[tracking].state_file` inside `archledger_dir` (default: `.archledger/source-state.json`). File entries persist normalized SHA-256 content hashes only; mtimes and file sizes are deliberately not stored. Directory hashes are derived from child file hashes.
