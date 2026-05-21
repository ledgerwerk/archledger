---
id: concept_0002
type: concept
title: "Config discovery and path resolution"
status: accepted
section: cross_cutting_concepts
order: 20
applies_to:
  - Storage Layer
  - CLI Layer
---

archledger discovers its project configuration by walking up from the current directory looking for `archledger.toml` or `.archledger.toml`. The `archledger_dir` setting in the config can be relative (resolved from the config file's directory) or absolute (used as-is). This allows the storage directory to live outside the source tree, for example in a separate state repository. All path resolution happens in `storage/paths.py`.
