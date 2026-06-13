---
schema_version: 2
id: diagram-0063
type: diagram
title: Deployment Topology
status: accepted
section: deployment_view
order: 40
date: "2026-05-22"
diagram_type: unicode
caption: archledger deployment nodes and their relationships
related_records:
  - deploy-0064
  - deploy-0065
  - deploy-0066
  - deploy-0067
  - deploy-0068
tags:
  - deployment
body_format: markdown
created_at: "2026-05-21T19:34:08Z"
updated_at: "2026-05-22T07:15:00Z"
kind: diagram
---

archledger has no server component. It runs as a local CLI tool on developer
machines and in CI runners. The storage directory is co-located with the source
repository.

```textdiagram
┌─ Developer Machine ───────────────────────────────────────────┐
│                                                               │
│  Python 3.10+ (venv / system)                                 │
│       │                                                       │
│  ┌────▼───────────┐   ┌──────────────┐  ┌──────────────────┐ │
│  │ archledger CLI │──>│  Workspace   │  │  Build Output    │ │
│  │ (console       │   │ .archledger/ │  │ ARCHITECTURE.md  │ │
│  │  script)       │   │  + source/   │  │  + exports       │ │
│  └────────────────┘   └──────────────┘  └──────────────────┘ │
│       │ optional                                              │
│  ┌────▼────────────────┐                                     │
│  │ pandoc / asciidoctor│                                     │
│  └─────────────────────┘                                     │
└───────────────────────────────────────────────────────────────┘

┌─ CI Runner ──────────────────────────────────────────────────┐
│  Python 3.10+ ──> archledger CLI ──> Build Artifacts        │
└────────────────────────────────┬─────────────────────────────┘
                                 │ publish
                                 ▼
                          ┌──────────────┐
                          │ Docs Hosting │
                          └──────────────┘

┌─ PyPI ──────────────┐
│ archledger wheel    │── pip install ──> Developer Machine
│                     │── pip install ──> CI Runner
└─────────────────────┘
```
