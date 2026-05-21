---
id: black_box_0003
type: black_box
title: "Render Layer"
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 30
interfaces:
  - build_document()
location:
  - archledger/render.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T05:52:15Z"
updated_at: "2026-05-20T12:00:00Z"
---

The render module (`render.py`) is a thin facade that orchestrates the build pipeline. It resolves requested output formats via the formats module, delegates document assembly to the Assembly Layer, and then delegates multi-format conversion to the Converter Layer. The actual rendering logic is split across the Assembly Layer (template orchestration) and the Section Rendering Layer (per-record-type output).
