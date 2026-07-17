---
id: strategy-0039
type: strategy_item
title: File-based record pipeline with dual-source and multi-format export
schema_version: 4
body_format: markdown
status: accepted
section: solution_strategy
order: 10
drivers:
  - Maintainability
  - Traceability
  - Reproducibility
constraints:
  - Markdown or AsciiDoc with YAML front matter as canonical source
  - No external database dependency
  - Typer CLI interface
related_adrs:
  - adr-0077
  - adr-0078
  - adr-0079
source_refs:
  - archledger/assembly.py
  - archledger/section_rendering.py
kind: strategy
version: 1
---

## Strategy

The core approach is a four-stage pipeline: author (create/edit Markdown or AsciiDoc records), validate (check integrity and completeness), assemble (render a single document using dialect-aware templates), and export (convert to requested formats via pandoc or asciidoctor). A source tracking subsystem enables change detection and impact analysis. A migration path allows converting from one source dialect to another. Each stage is independent and stateless except for the shared filesystem. The CLI orchestrates the pipeline and the Repository implements the business logic.

## Trade-offs

- Positive: simple mental model, easy to automate, no server dependency, supports both major documentation formats.
- Negative: no concurrent write protection, no real-time collaboration, referential integrity only checked on demand, external converter dependency for non-native formats.
