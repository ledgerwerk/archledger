---
schema_version: 2
id: diagram_0001
type: diagram
title: "System Context"
status: accepted
section: context_and_scope
order: 10
date: "2026-05-21"
diagram_type: "mermaid"
caption: "archledger system context showing external actors and adjacent systems"

related_records:
  - context_interface_0001
  - context_interface_0002
  - context_interface_0003
  - context_interface_0004

tags:
  - context
body_format: markdown
created_at: "2026-05-21T19:33:47Z"
updated_at: "2026-05-21T19:35:00Z"
---

archledger operates as a local CLI tool. External actors interact through shell invocations. Optional converter tools (pandoc, asciidoctor) are invoked as subprocesses for non-native export formats.

```mermaid
graph TB
    Developer["fa:fa-user Developer"]
    Agent["fa:fa-robot Coding Agent"]
    CI["fa:fa-server CI Pipeline"]

    CLI["archledger CLI\n(Typer entrypoint)"]

    Workspace["Project Workspace\n.archledger/ records/"]
    Output["Build Output\nARCHITECTURE.md / exports"]

    Pandoc["pandoc\n(optional)"]
    Asciidoctor["asciidoctor / asciidoctor-pdf\n(optional)"]

    Developer -->|"CLI invocation"| CLI
    Agent -->|"CLI --json"| CLI
    CI -->|"exit codes + artifacts"| CLI

    CLI -->|"read config & records"| Workspace
    CLI -->|"write assembled doc"| Output

    CLI -->|"subprocess"| Pandoc
    CLI -->|"subprocess"| Asciidoctor

    style CLI fill:#4a9eff,color:#fff
    style Workspace fill:#e8f4fd
    style Output fill:#e8f4fd
    style Pandoc fill:#f0f0f0,stroke-dasharray: 5 5
    style Asciidoctor fill:#f0f0f0,stroke-dasharray: 5 5
```
