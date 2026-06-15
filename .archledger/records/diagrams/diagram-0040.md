---
schema_version: 4
id: diagram-0040
type: diagram
title: Building Block Layer Structure
status: accepted
section: building_block_view
order: 20
diagram_type: unicode
caption: Layered decomposition of archledger building blocks
related_records:
  - block-0041
  - block-0042
  - block-0043
  - block-0044
  - block-0045
  - block-0046
  - block-0047
  - block-0048
  - block-0049
  - block-0050
  - block-0051
  - block-0052
  - block-0053
  - block-0054
  - block-0055
  - block-0056
tags:
  - building-block
  - layers
body_format: markdown
kind: diagram
version: 1
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
