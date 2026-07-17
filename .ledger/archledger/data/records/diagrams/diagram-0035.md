---
schema_version: 4
id: diagram-0035
type: diagram
title: System Context
status: accepted
section: context_and_scope
order: 10
diagram_type: unicode
caption: archledger system context showing external actors and adjacent systems
related_records:
  - context-0034
  - context-0036
  - context-0037
  - context-0038
tags:
  - context
body_format: markdown
kind: diagram
version: 1
---

archledger operates as a local CLI tool. External actors interact through shell invocations. Optional converter tools (pandoc, asciidoctor) are invoked as subprocesses for non-native export formats.

```textdiagram
┌───────────┐  ┌──────────────┐  ┌──────────────┐
│ Developer │  │ Coding Agent │  │ CI Pipeline  │
└─────┬─────┘  └──────┬───────┘  └──────┬───────┘
      │               │                 │
      └───────────────┼─────────────────┘
                      ▼
           ┌─────────────────────┐
           │   archledger CLI    │
           │  (Typer entrypoint) │
           └─────┬─────────┬─────┘
                 │         │
      ┌──────────▼───┐ ┌───▼──────────────┐
      │  Workspace   │ │  Build Output    │
      │ .archledger/ │ │ ARCHITECTURE.md  │
      │  records/    │ │  + exports       │
      └──────────────┘ └───┬──────────┬────┘
                             │          │
                      ┌──────▼───┐ ┌───▼───────────┐
                      │  pandoc  │ │ asciidoctor   │
                      │ optional │ │   optional    │
                      └──────────┘ └──────────────┘
```
