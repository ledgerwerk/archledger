---
id: concept-0071
type: concept
title: Record lifecycle and status
schema_version: 4
body_format: markdown
status: accepted
section: cross_cutting_concepts
order: 10
applies_to:
  - Repository Layer
  - CLI Layer
source_refs:
  - README.md
  - archledger/section_rendering.py
kind: concept
version: 1
---

Every record has a status field that controls its lifecycle: `draft` (incomplete, excluded from default builds), `proposed` (visible but not formally confirmed), `accepted` (confirmed, included by default), `deprecated` (visible but no longer preferred), and `superseded` (hidden unless explicitly included). The `check` command warns about draft records and empty sections. The `build` command only includes records with visible statuses by default; `--include-draft` and `--include-superseded` flags override this.
