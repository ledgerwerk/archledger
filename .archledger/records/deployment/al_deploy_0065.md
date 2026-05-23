---
id: al_deploy_0065
type: infrastructure
title: CI pipeline
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: deployment_view
level: 1
parent: null
order: 20
environment: production
maps_building_blocks:
  - CLI Layer
  - Repository Layer
source_refs:
  - pyproject.toml
  - docs/index.rst
---

CI runners execute `archledger check` to validate record integrity and `archledger build --output docs/architecture.md` to produce the rendered document. The built Markdown file is published as a CI artifact. Non-zero exit codes from `check` fail the pipeline.
