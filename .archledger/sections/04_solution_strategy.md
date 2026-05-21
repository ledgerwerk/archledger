---
id: section_solution_strategy
type: section
section: solution_strategy
title: Solution Strategy
order: 40
status: accepted
---

The fundamental approach is a file-based pipeline: human-editable Markdown or AsciiDoc records with YAML front matter are stored in a configurable directory, validated by a check command, assembled into a single arc42-style document by a Jinja2-based render step, and optionally converted to other formats (HTML, PDF, DOCX, RST, Textile) via pandoc or asciidoctor. A dialect abstraction (`dialects.py`) ensures that rendering logic works identically for both source formats. The CLI provides the sole interface. No server, database, or GUI is involved.

A source tracking subsystem (snapshot/changed) allows agents to detect which source files changed since the last baseline and which architecture records are impacted via `source_refs` linkage.
