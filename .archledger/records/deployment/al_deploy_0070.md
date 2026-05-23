---
schema_version: 2
id: al_deploy_0070
type: infrastructure
title: CI release validation
status: accepted
section: deployment_view
level: 1
parent: null
order: 70
date: "2026-05-21"
environment: ci
maps_building_blocks: []
body_format: markdown
created_at: "2026-05-21T18:18:49Z"
updated_at: "2026-05-21T18:18:49Z"
source_refs:
  - pyproject.toml
  - docs/index.rst
---

CI release validation runs unit tests, package build checks, version consistency checks, and release workflow documentation checks before publishing.
