---
schema_version: 2
id: al_deploy_0067
type: infrastructure
title: Console script entry point
status: accepted
section: deployment_view
level: 1
parent: null
order: 40
date: "2026-05-21"
environment: runtime
maps_building_blocks: []
body_format: markdown
created_at: "2026-05-21T18:18:47Z"
updated_at: "2026-05-21T18:18:47Z"
source_refs:
  - pyproject.toml
  - docs/index.rst
---

The runtime entry point is the console script `archledger = "archledger.launcher:main"`, installed via package metadata and executed in local/CI environments.
