---
schema_version: 4
id: deploy-0067
type: infrastructure
title: Console script entry point
status: accepted
section: deployment_view
level: 1
parent: null
order: 40
environment: runtime
maps_building_blocks: []
body_format: markdown
source_refs:
  - pyproject.toml
  - docs/index.rst
kind: deploy
version: 1
---

The runtime entry point is the console script `archledger = "archledger.launcher:main"`, installed via package metadata and executed in local/CI environments.
