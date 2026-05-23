---
schema_version: 2
id: al_diagram_0040
type: diagram
title: Building Block Layer Structure
status: accepted
section: building_block_view
order: 20
date: "2026-05-22"
diagram_type: unicode
caption: Layered decomposition of archledger building blocks
related_records:
  - al_block_0041
  - al_block_0042
  - al_block_0043
  - al_block_0044
  - al_block_0045
  - al_block_0046
  - al_block_0047
  - al_block_0048
  - al_block_0049
  - al_block_0050
  - al_block_0051
  - al_block_0052
  - al_block_0053
  - al_block_0054
  - al_block_0055
  - al_block_0056
tags:
  - building-block
  - layers
body_format: markdown
created_at: "2026-05-21T19:33:57Z"
updated_at: "2026-05-22T07:15:00Z"
---

The system is organized as a layered pipeline. User input flows down from the
CLI through business logic to storage. Rendering flows upward from storage
through assembly to the build output.

```textdiagram
┌─ Interface ──────────────────────────────────────────────────┐
│  CLI Layer  (cli.py, cli_formatting.py, cli_payloads.py)    │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Business Logic ────────────────────────────────────────────┐
│  Repository (repo.py)        Model (model.py)               │
│  Record Types (rec_types)    Checks (checks.py)             │
│  Source Refs (source_refs.py)                               │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Configuration ────────────────────────────────────────────┐
│  Config Layer (config/)                                    │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Rendering ────────────────────────────────────────────────┐
│  Render (render.py)       Assembly (assembly.py)           │
│  Dialect (dialects.py)    Section Rendering                │
│                           (section_rendering.py)            │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Export ───────────────────────────────────────────────────┐
│  Converter (converters, conversion_plan, formats)          │
│  Migration (migration.py)                                  │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Infrastructure ───────────────────────────────────────────┐
│  Storage (storage/)         Source Tracking                 │
│                             (source_tracking.py)            │
└────────────────────────────────────────────────────────────┘
```
