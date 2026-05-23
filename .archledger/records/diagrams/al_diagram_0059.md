---
schema_version: 2
id: al_diagram_0059
type: diagram
title: Build Pipeline Flow
status: accepted
section: runtime_view
order: 30
date: "2026-05-22"
diagram_type: text
caption: The four-stage pipeline from authoring to export
related_records:
  - al_runtime_0057
  - al_runtime_0061
  - al_strategy_0039
tags:
  - pipeline
  - runtime
body_format: markdown
created_at: "2026-05-21T19:34:02Z"
updated_at: "2026-05-22T07:15:00Z"
---

The build pipeline processes architecture records through four stages. Native
Markdown and AsciiDoc builds require no external tools. Non-native exports
delegate to pandoc or asciidoctor.

```textdiagram
┌──────────┐      ┌───────────┐      ┌────────────┐      ┌──────────┐
│  Author  │─────>│ Validate  │─────>│  Assemble  │─────>│  Export  │
├──────────┤      ├───────────┤      ├────────────┤      ├──────────┤
│          │      │ Parse     │      │ Load recs  │      │ Plan     │
│ Create / │      │ front     │      │ & sections │      │ conver-  │
│ edit     │      │ matter    │      │            │      │ sion     │
│ record   │      │           │      │ Resolve    │      │          │
│ files    │      │ Check     │      │ dialect    │      │ Native?  │
│          │      │ schema +  │      │            │      │  yes:    │
│          │      │ cross-    │      │ Render     │      │   copy   │
│          │      │ refs      │      │ Jinja2     │      │  no:     │
│          │      │           │      │ template   │      │   pandoc │
│          │      │ Type-     │      │            │      │   or     │
│          │      │ specific  │      │ Write      │      │   asc-   │
│          │      │ checks    │      │ native doc │      │   iido-  │
│          │      │           │      │            │      │   ctor   │
└──────────┘      └───────────┘      └────────────┘      └──────────┘
    new              check             build              build
                                      --format            --format
```
