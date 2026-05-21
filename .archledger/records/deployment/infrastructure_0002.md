---
id: infrastructure_0002
type: infrastructure
title: "CI pipeline"
status: accepted
section: deployment_view
level: 1
parent: null
order: 20
environment: "production"
maps_building_blocks:
  - CLI Layer
  - Repository Layer
---

CI runners execute `archledger check` to validate record integrity and `archledger build --output docs/architecture.md` to produce the rendered document. The built Markdown file is published as a CI artifact. Non-zero exit codes from `check` fail the pipeline.
