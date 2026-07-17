---
schema_version: 4
id: block-0053
type: black_box
title: Config Layer
status: accepted
section: building_block_view
level: 1
parent: block-0041
order: 105
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
source_refs:
  - path: archledger/config/
    reason: Config subpackage with model, parse, render
  - docs/configuration.md
  - docs/source-model.md
kind: block
version: 2
---

The `config` subpackage owns all project configuration concerns. `config/model.py` defines frozen dataclasses for each configuration domain: `SourceConfig`, `BuildConfig` (with nested `BuildOutputConfig`), `Arc42Config`, `SkillConfig`, `TrackingConfig`, and the unified `ProjectConfig` facade that composes them via properties. It also exports public allowed-value constants (`VALID_BUILD_CONVERTERS`, `VALID_DIAGRAM_RENDERERS`, `VALID_DIAGRAM_TYPES`, `VALID_DIAGRAM_IMAGE_FORMATS`, `VALID_TRACKING_SCANNERS`) shared by `parse.py`, `render.py`, and `cli.py`.

`ProjectConfig` includes ID format fields: `id_prefix` (default `al`), `id_width` (default `4`), `id_segment_mode` (default `none`), `id_default_segment`, and `id_segment_map`. The `id_format` property constructs a `LedgerIdFormat` instance from these fields, providing the canonical ID formatting object used throughout the repository, check, and renumber layers.

`config/parse.py` loads and validates `archledger.toml` using `tomllib` (or `tomli` for Python < 3.11), with strict key validation and environment variable expansion. It parses the `[ids]` section, validating prefix, width, segment mode, and segment map using validators from `ids.py`. `config/render.py` generates default configuration files for `archledger init` via a two-stage pipeline: `build_default_project_config()` constructs a validated `ProjectConfig` dataclass from init parameters (including build, diagram, arc42, tracking, and ID format options), and `render_project_config()` serializes it to TOML.

The `[diagrams]` section supports five diagram types (`text`, `ascii`, `unicode`, `svgbob`, `mermaid`) and three renderers (`pass-through`, `mermaid-cli`, `asciidoctor-diagram`). The default diagram type is `text`, ensuring that new diagram records produce readable text-based diagrams in native builds without any external tooling.

The `[ids]` section (config version 7+) configures the ledger ID format: `prefix`, `width`, `segment_mode`, `default_segment`, and `segment_map`. Projects created without this section fall back to `al` prefix, width 4, and `none` segment mode, preserving backward compatibility.
