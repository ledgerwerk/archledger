---
id: section_architecture_constraints
type: section
section: architecture_constraints
title: Architecture Constraints
order: 20
status: accepted
---

archledger operates under several technical constraints that shape its architecture: Python 3.10+ as the runtime, Markdown and AsciiDoc as first-class source formats with YAML front matter, filesystem-only storage (no database), Typer as the CLI framework, and optional external converters (pandoc, asciidoctor) for multi-format exports. These constraints keep the tool lightweight, portable, and easy to automate.
