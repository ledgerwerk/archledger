---
id: black_box_0006
type: black_box
title: Assembly Layer
schema_version: 2
date: "2026-05-20"
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 60
interfaces:
  - assemble_document()
  - assemble_asciidoc_document()
location:
  - archledger/assembly.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T12:00:00Z"
updated_at: "2026-05-20T12:00:00Z"
source_refs:
  - archledger/assembly.py
---

The assembly module loads all records from the repository, groups them by arc42 section, filters by visibility, selects the correct dialect, and renders a single document using a Jinja2 template (`arc42_document.md.j2` or `arc42_document.adoc.j2`). It delegates to the Section Rendering Layer for per-record-type output formatting. The assembly runs a check first and blocks the build if errors are found.
