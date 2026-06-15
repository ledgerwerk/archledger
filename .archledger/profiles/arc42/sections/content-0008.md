---
id: content-0008
type: section
section: cross_cutting_concepts
title: Cross-cutting Concepts
schema_version: 4
body_format: markdown
order: 80
status: accepted
kind: content
version: 1
---

Four cross-cutting concepts pervade the architecture: the record lifecycle (draft, proposed, accepted, deprecated, superseded) which controls visibility and validation behavior, the config discovery mechanism which resolves project paths from the workspace directory upward, the dialect abstraction which ensures format-neutral rendering for both Markdown and AsciiDoc sources, and the multi-type diagram record system which supports text, ascii, unicode, svgbob, and mermaid diagram types with type-appropriate validation and templating.

A fourth cross-cutting concern is source tracking and change impact analysis, which is visualized in the [Source Tracking Flow diagram](#diagram-al_diagram_0076).
