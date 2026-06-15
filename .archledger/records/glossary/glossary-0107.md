---
id: glossary-0107
type: glossary_term
title: Front Matter
schema_version: 4
body_format: markdown
status: accepted
section: glossary
order: 30
term: Front Matter
definition:
  The YAML block at the top of a Markdown record file, delimited by ---,
  containing machine-readable metadata fields. Parsed by archledger's frontmatter
  module to populate the ArchitectureRecord dataclass.
source_refs:
  - README.md
  - docs/agent-workflow.rst
kind: glossary
version: 1
---

The YAML block delimited by `---` at the top of a Markdown record file. Contains machine-readable metadata fields such as id, type, title, status, section, order, and type-specific fields. Parsed by archledger's frontmatter module to populate the ArchitectureRecord dataclass.
