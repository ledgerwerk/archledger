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
  - block-0141
tags:
  - building-block
  - layers
body_format: markdown
kind: diagram
version: 2
---

The CLI coordinates read paths through the Repository and write paths through
the Record Mutation Service. Shared model and registry contracts govern both.
Rendering and evidence-query services consume the same canonical storage.

```textdiagram
┌─ Interface ───────────────────────────────────────────────────┐
│ CLI, payload formatting, human formatting                    │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Source-model services ───────────────────────────────────────┐
│ Repository │ Model │ Record Types │ Checks │ Mutations        │
│ Source refs │ Test refs │ Links │ Scopes │ ID services       │
└────────────────────────────┬─────────────────────────────────┘
                             ▼
┌─ Persistence and configuration ───────────────────────────────┐
│ Config │ Front matter │ Storage │ Archive │ Source state      │
└───────────────┬─────────────────────────────┬─────────────────┘
                ▼                             ▼
┌─ Document pipeline ────────────┐  ┌─ Evidence pipeline ──────┐
│ Assembly │ Dialects │ Sections │  │ Source Tracking          │
│ Render │ Diagrams │ Converters │  │ Context │ Trace │ Combo  │
└───────────────┬────────────────┘  └───────────────────────────┘
                ▼
       Native document and optional exports
```
