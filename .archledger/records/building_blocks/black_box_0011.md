---
id: black_box_0011
type: black_box
title: "Migration Layer"
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 95
interfaces:
  - convert_sources()
location:
  - archledger/migration.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T12:00:00Z"
updated_at: "2026-05-20T12:00:00Z"
---

The migration module converts source fragments from one dialect to another. Currently supports Markdown-to-AsciiDoc conversion. It iterates over all section and record files, converts the body using pandoc (falling back to keeping the original body if pandoc is unavailable), updates the YAML front matter to reflect the new body format, and optionally replaces the original files. It also rewrites the project config to target the new source format.
