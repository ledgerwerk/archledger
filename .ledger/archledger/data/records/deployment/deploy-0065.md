---
id: deploy-0065
type: infrastructure
title: CI pipeline
schema_version: 4
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
  - docs/index.md
kind: deploy
version: 2
---

CI runners execute `archledger check` to validate record integrity and `archledger build --output docs/architecture.md` to produce the rendered document. The built Markdown file is published as a CI artifact. Non-zero exit codes from `check` fail the pipeline.
