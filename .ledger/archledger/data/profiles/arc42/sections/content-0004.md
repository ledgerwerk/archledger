---
id: content-0004
type: section
section: solution_strategy
title: Solution Strategy
schema_version: 4
body_format: markdown
order: 40
status: accepted
kind: content
version: 2
---

The fundamental approach is a file-based pipeline: human-editable Markdown or
AsciiDoc records with YAML front matter are validated, assembled into an arc42
document with Jinja2, and optionally converted through pandoc or asciidoctor. A
dialect abstraction keeps rendering independent of the source format. The CLI
is the sole product interface; there is no server, database, or GUI.

A typed record registry describes per-record metadata shapes. Existing records
are changed through version-aware mutation commands. Complete-document apply
operations validate identity and kind, increment versions only for real changes,
and roll back the target when repository validation fails.

Source tracking compares the workspace with an explicit snapshot and maps
changed files to architecture records through `source_refs`. Focused context and
trace queries expose bounded architecture evidence without requiring a build.
Archledger deliberately remains isolated from behavior-specification and
cross-ledger workflow semantics.
