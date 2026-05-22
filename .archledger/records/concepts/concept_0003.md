---
id: concept_0003
type: concept
title: "Dialect abstraction for dual-source support"
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: cross_cutting_concepts
order: 30
applies_to:
  - Dialect Layer
  - Section Rendering Layer
  - Assembly Layer
source_refs:
  - README.md
  - archledger/section_rendering.py
---

archledger supports both Markdown and AsciiDoc as first-class source formats. The dialect abstraction (`dialects.py`) defines a `Dialect` base class with methods for headings, tables, bullets, and strong text. `MarkdownDialect` and `AsciiDocDialect` implement these using their respective markup conventions. All rendering code in the Section Rendering Layer and Assembly Layer uses dialects rather than hardcoded markup, ensuring that a single rendering codebase produces correct output for both source formats. Templates exist in both `.md.j2` and `.adoc.j2` variants.
