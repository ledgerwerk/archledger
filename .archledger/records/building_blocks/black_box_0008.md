---
id: black_box_0008
type: black_box
title: Section Rendering Layer
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 75
interfaces:
- section_body()
- building_block_hierarchy()
- adr_sections()
- quality_scenarios()
- risk_table()
- glossary_table()
- (and other per-type renderers)
location:
- archledger/section_rendering.py
fulfilled_requirements: []
risks: []
tags: []
created_at: '2026-05-20T12:00:00Z'
updated_at: '2026-05-20T12:00:00Z'
source_refs:
- archledger/section_rendering.py
---

The section rendering module contains all per-record-type rendering functions. Each function takes a list of `ArchitectureRecord` and a `Dialect`, and returns a format-appropriate string (Markdown or AsciiDoc). Functions include table renderers (quality goals, stakeholders, quality scenarios, risks, glossary), list renderers (constraints, context interfaces), hierarchy renderers (building blocks with white/black boxes and interfaces), and prose renderers (ADRs, runtime scenarios, deployment, concepts, strategy items).
