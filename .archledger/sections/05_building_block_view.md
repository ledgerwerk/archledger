---
id: section_building_block_view
type: section
section: building_block_view
title: Building Block View
schema_version: 2
date: "2026-05-21"
body_format: markdown
order: 50
status: accepted
---

The system is decomposed into fifteen black boxes within a single white box. The CLI Layer receives user input and delegates output formatting, the Config Layer parses and renders project configuration, the Repository Layer orchestrates business logic, the Model Layer defines core data structures and validation, the Record Type Registry maps record types to templates and defaults, the Check Layer validates record content per type, the Source Ref Validation layer normalizes traceability links, the Storage Layer handles file I/O, the Assembly Layer renders the document via Jinja2 templates, the Dialect Layer abstracts format-specific markup, the Section Rendering Layer handles per-record-type output, the Render Layer orchestrates the build pipeline, the Converter Layer handles multi-format export, the Source Tracking Layer detects changes and impacts, and the Migration Layer converts between source dialects.

See the [Building Block Layer Structure diagram](#diagram-diagram_0002) for a visual decomposition showing the layer relationships.
