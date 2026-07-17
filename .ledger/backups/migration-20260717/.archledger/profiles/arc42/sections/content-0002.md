---
id: content-0002
type: section
section: architecture_constraints
title: Architecture Constraints
schema_version: 4
body_format: markdown
order: 20
status: accepted
kind: content
version: 1
---

archledger operates under several technical constraints that shape its architecture: Python 3.10+ as the runtime, Markdown and AsciiDoc as first-class source formats with YAML front matter, filesystem-only storage (no database), Typer as the CLI framework, and optional external converters (pandoc, asciidoctor) for multi-format exports. These constraints keep the tool lightweight, portable, and easy to automate.
