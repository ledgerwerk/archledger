---
id: glossary_0001
type: glossary_term
title: "Architecture Record"
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: glossary
order: 10
term: "Architecture Record"
definition: "A Markdown or AsciiDoc file with YAML front matter that describes one architecture element: a requirement, stakeholder, quality goal, constraint, context interface, strategy item, building block, runtime scenario, infrastructure, concept, ADR, quality requirement, quality scenario, risk, or glossary term."
source_refs:
  - README.md
  - docs/agent-workflow.rst
---

A Markdown or AsciiDoc file with YAML front matter that describes one architecture element. Each record has an id, type, title, status, section, order, body_format, and optional source_refs linking it to source code artifacts.
