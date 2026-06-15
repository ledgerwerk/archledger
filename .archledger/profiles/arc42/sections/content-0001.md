---
id: content-0001
type: section
section: introduction_and_goals
title: Introduction and Goals
schema_version: 4
body_format: markdown
order: 10
status: accepted
kind: content
version: 1
---

archledger is a dual-source architecture documentation ledger for arc42-style documents. Both Markdown and AsciiDoc are first-class source formats. The tool keeps project-local configuration (`archledger.toml`) in the source workspace and stores human-editable architecture records as individual files with YAML front matter. The primary output is a rendered document assembled from these records, with optional exports to HTML, PDF, DOCX, RST, and Textile via pandoc or asciidoctor.

The tool targets three stakeholders: developers who document alongside code, architects who maintain the structural vision, and coding agents that automate documentation workflows via the CLI.

## How to update this architecture

Use the source-first maintenance loop:

```bash
archledger source changed --json
archledger read --json --body
archledger new <type> "<title>" --status accepted
archledger check --strict
archledger build
```

Detailed agent guidance lives in `docs/agent-workflow.rst`.
