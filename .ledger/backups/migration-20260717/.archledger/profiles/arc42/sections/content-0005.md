---
id: content-0005
type: section
section: building_block_view
title: Building Block View
schema_version: 4
body_format: markdown
order: 50
status: accepted
kind: content
version: 2
---

The system is one white box composed of focused services. The CLI layer parses
commands and presents human or JSON results. Config and Storage resolve project
paths and persist front-matter records. Repository and Model load records and
enforce structural, metadata-shape, and cross-reference rules. The Record Type
Registry supplies type-specific metadata contracts and templates. The Record
Mutation Service performs versioned, validated writes with rollback.

Assembly, Dialect, Section Rendering, Render, and Converter services build native
or converted documents. Source Tracking reports drift and impact. Context and
Trace provide bounded architecture evidence. Migration, identity, renumbering,
ID sequence, and segment services preserve source-model integrity. Diagram,
source-ref, test-ref, link, scope, and check services validate specialized
contracts.

See the [Building Block Layer Structure diagram](#diagram-al_diagram_0040) for a
visual decomposition of the principal layer relationships.
