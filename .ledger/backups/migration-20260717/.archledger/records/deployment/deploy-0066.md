---
schema_version: 4
id: deploy-0066
type: infrastructure
title: PyPI and wheel installation
status: accepted
section: deployment_view
level: 1
parent: null
order: 30
environment: release
maps_building_blocks: []
body_format: markdown
source_refs:
  - pyproject.toml
  - docs/index.md
kind: deploy
version: 2
---

Distribution targets are PyPI source/wheel artifacts built from this repository. Release pipelines build wheel/sdist and publish versioned packages for installation with `pip install archledger`.
