---
id: context_interface_0001
type: context_interface
title: "Source repository"
status: accepted
section: context_and_scope
order: 10
context_kind: "technical"
partner: "Source repository"
inputs:
  - archledger.toml configuration
  - Markdown record files in archledger_dir
outputs:
  - Generated architecture.md build output
  - Updated record files (new, edited)
channels:
  - Local filesystem
---

The source repository hosts the `archledger.toml` config and the architecture record files. archledger reads records from disk and writes the rendered document back to the repository's build directory or a specified output path.
