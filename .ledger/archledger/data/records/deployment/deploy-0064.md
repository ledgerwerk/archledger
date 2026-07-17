---
id: deploy-0064
type: infrastructure
title: Local development
schema_version: 4
body_format: markdown
status: accepted
section: deployment_view
level: 1
parent: null
order: 10
environment: development
maps_building_blocks:
  - CLI Layer
  - Repository Layer
  - Storage Layer
  - Render Layer
source_refs:
  - pyproject.toml
  - docs/index.md
kind: deploy
version: 2
---

Developer machine with Python >= 3.10. archledger is installed via `pip install -e .` in a virtual environment. The project directory contains `archledger.toml` at the root. The storage directory (default `.archledger/`) holds sections, records, and build output. No network access, database, or server process is required.
