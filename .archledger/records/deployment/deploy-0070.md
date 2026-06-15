---
schema_version: 4
id: deploy-0070
type: infrastructure
title: CI release validation
status: accepted
section: deployment_view
level: 1
parent: null
order: 70
environment: ci
maps_building_blocks: []
body_format: markdown
source_refs:
  - pyproject.toml
  - docs/index.rst
kind: deploy
version: 1
---

CI release validation runs unit tests, package build checks, version consistency checks, and release workflow documentation checks before publishing.
