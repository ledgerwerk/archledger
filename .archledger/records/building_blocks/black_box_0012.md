---
schema_version: 2
id: black_box_0012
type: black_box
title: Config Layer
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 105
date: "2026-05-21"
interfaces:
  - load_project_config()
  - render_default_config()
  - ProjectConfig dataclass
location:
  - archledger/config/__init__.py
  - archledger/config/model.py
  - archledger/config/parse.py
  - archledger/config/render.py
fulfilled_requirements: []
risks: []
tags: []
body_format: markdown
created_at: "2026-05-21T11:30:43Z"
updated_at: "2026-05-21T11:30:43Z"
source_refs:
  - path: archledger/config/
    reason: Config subpackage with model, parse, render
---

The `config` subpackage owns all project configuration concerns. `config/model.py` defines frozen dataclasses for each configuration domain: `SourceConfig`, `BuildConfig` (with nested `BuildOutputConfig`), `Arc42Config`, `SkillConfig`, `TrackingConfig`, and the unified `ProjectConfig` facade that composes them via properties. `config/parse.py` loads and validates `archledger.toml` using `tomllib` (or `tomli` for Python < 3.11), with strict key validation and environment variable expansion. `config/render.py` generates default configuration files for `archledger init`. The subpackage re-exports key types from `__init__.py`.
