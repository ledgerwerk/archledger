---
schema_version: 2
id: al_block_0053
type: black_box
title: Config Layer
status: accepted
section: building_block_view
level: 1
parent: al_block_0041
order: 105
date: "2026-05-21"
interfaces:
  - load_project_config()
  - build_default_project_config()
  - render_project_config()
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
updated_at: "2026-05-22T21:45:00Z"
source_refs:
  - path: archledger/config/
    reason: Config subpackage with model, parse, render
---

The `config` subpackage owns all project configuration concerns. `config/model.py` defines frozen dataclasses for each configuration domain: `SourceConfig`, `BuildConfig` (with nested `BuildOutputConfig`), `Arc42Config`, `SkillConfig`, `TrackingConfig`, and the unified `ProjectConfig` facade that composes them via properties. It also exports public allowed-value constants (`VALID_BUILD_CONVERTERS`, `VALID_DIAGRAM_RENDERERS`, `VALID_DIAGRAM_TYPES`, `VALID_DIAGRAM_IMAGE_FORMATS`, `VALID_TRACKING_SCANNERS`) shared by `parse.py`, `render.py`, and `cli.py`.

`config/parse.py` loads and validates `archledger.toml` using `tomllib` (or `tomli` for Python < 3.11), with strict key validation and environment variable expansion. `config/render.py` generates default configuration files for `archledger init` via a two-stage pipeline: `build_default_project_config()` constructs a validated `ProjectConfig` dataclass from init parameters (including build, diagram, arc42, and tracking options), and `render_project_config()` serializes it to TOML.

The `[diagrams]` section supports five diagram types (`text`, `ascii`, `unicode`, `svgbob`, `mermaid`) and three renderers (`pass-through`, `mermaid-cli`, `asciidoctor-diagram`). The default diagram type is `text`, ensuring that new diagram records produce readable text-based diagrams in native builds without any external tooling.
