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
version: 3
---

archledger is a source-first architecture documentation ledger for arc42-style
documents. Markdown and AsciiDoc are first-class source formats. Project-local
configuration selects the storage paths, while human-editable architecture
records use YAML front matter and versioned bodies. Native builds assemble these
records directly; optional converters produce HTML, PDF, DOCX, RST, or Textile.

The tool targets developers, architects, and coding agents. Its scope is
architecture records, links, and source evidence. Behavior specifications are
maintained by SpecMason, and lifecycle or cross-ledger orchestration remains
outside Archledger.

## How to update this architecture

Use the source-first maintenance loop:

```bash
archledger --json source changed
archledger --json context --changed
archledger record export RECORD_ID --output /tmp/record.md
# edit /tmp/record.md
archledger record apply RECORD_ID --from-file /tmp/record.md
archledger --json check --strict
archledger --json source snapshot --reason after-archledger-update
```

Detailed agent guidance lives in `docs/agent-workflow.md`.
