---
id: block-0044
type: black_box
title: Render Layer
schema_version: 4
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: block-0041
order: 30
interfaces:
  - build_document()
location:
  - archledger/render.py
fulfilled_requirements: []
risks: []
tags: []
source_refs:
  - archledger/render.py
kind: block
version: 1
---

The render module (`render.py`) is a thin facade that orchestrates the build pipeline. It resolves requested output formats via the formats module, delegates document assembly to the Assembly Layer, and then delegates multi-format conversion to the Converter Layer. The actual rendering logic is split across the Assembly Layer (template orchestration) and the Section Rendering Layer (per-record-type output).
