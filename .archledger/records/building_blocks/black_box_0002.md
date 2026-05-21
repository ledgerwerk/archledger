---
id: black_box_0002
type: black_box
title: "Repository Layer"
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 20
interfaces:
  - create_record()
  - list_records()
  - get_record()
  - load_all_records()
  - check()
  - init()
  - status()
location:
  - archledger/repository.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T05:52:15Z"
updated_at: "2026-05-20T12:00:00Z"
---

The `ArchitectureRepository` class is the central business logic layer. It orchestrates record creation (allocating IDs, rendering templates, writing files), record loading (parsing front matter, validating fields, normalizing source refs), integrity checks (cross-reference validation, placeholder detection, source contract validation, body syntax warnings), and initialization (directory scaffolding, section file generation). It holds a Jinja2 environment for template rendering and enforces per-record-type content warnings.
