---
schema_version: 4
id: diagram-0059
type: diagram
title: Build Pipeline Flow
status: accepted
section: runtime_view
order: 30
diagram_type: text
caption: The four-stage pipeline from authoring to export
related_records:
  - runtime-0057
  - runtime-0061
  - strategy-0039
tags:
  - pipeline
  - runtime
body_format: markdown
kind: diagram
version: 1
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
