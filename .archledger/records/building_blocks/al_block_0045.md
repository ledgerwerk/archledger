---
id: al_block_0045
type: black_box
title: Storage Layer
schema_version: 2
date: "2026-05-20"
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: al_block_0041
order: 40
interfaces:
  - read_text() / write_text()
  - read_markdown_front_matter()
  - resolve_project_paths()
  - read_source_state() / write_source_state()
location:
  - archledger/storage/common.py
  - archledger/storage/frontmatter.py
  - archledger/storage/meta.py
  - archledger/storage/paths.py
  - archledger/storage/source_state.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T05:52:15Z"
updated_at: "2026-05-20T12:00:00Z"
source_refs:
  - archledger/storage/
---

The storage subpackage handles all file system I/O. `paths.py` discovers the project config and resolves directory layout (including `source_state_path` for tracking baselines). `project_config.py` holds the `ProjectConfig` dataclass with all configuration fields (source, build, arc42, skill, tracking). Config parsing and TOML loading now lives in the Config Layer (`config/` subpackage). `frontmatter.py` parses Markdown/AsciiDoc files with YAML front matter into metadata dict and body string, and provides `iter_source_files` for directory enumeration. `meta.py` manages the storage metadata file (`storage.yaml`). `source_state.py` reads and writes source tracking state as JSON. `common.py` provides `write_text`, `read_text`, `ensure_dir`, and `utc_now_iso`.
