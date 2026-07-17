---
id: content-0009
type: section
section: architecture_decisions
title: Architecture Decisions
schema_version: 4
body_format: markdown
order: 90
status: accepted
kind: content
version: 1
---

Key architectural decisions: dual-source support (Markdown and AsciiDoc as first-class formats), Markdown/AsciiDoc records with YAML front matter as the storage format, Typer as the CLI framework, Jinja2 for document rendering, and optional external converters for multi-format export. Each decision was driven by the goals of maintainability, traceability, and reproducibility.
