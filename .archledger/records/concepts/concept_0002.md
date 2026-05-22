---
id: concept_0002
type: concept
title: "Config discovery and path resolution"
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: cross_cutting_concepts
order: 20
applies_to:
  - Storage Layer
  - CLI Layer
  - Config Layer
source_refs:
  - README.md
  - archledger/section_rendering.py
---

archledger discovers its project configuration by walking up from the current directory looking for `archledger.toml` or `.archledger.toml`. The `archledger_dir` setting in the config can be relative (resolved from the config file's directory) or absolute (used as-is). This allows the storage directory to live outside the source tree, for example in a separate state repository.

Config parsing is handled by the Config Layer (`config/` subpackage): `config/parse.py` loads and validates the TOML file, `config/model.py` defines typed dataclasses for each configuration domain (source, build, arc42, skill, tracking), and `config/render.py` generates default configuration files for `archledger init`. Path resolution happens in `storage/paths.py`.
