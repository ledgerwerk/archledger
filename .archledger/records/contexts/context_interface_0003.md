---
id: context_interface_0003
type: context_interface
title: "CI pipeline"
status: accepted
section: context_and_scope
order: 30
context_kind: "technical"
partner: "CI runner"
inputs:
  - archledger check result
  - archledger build output
outputs:
  - CI pass/fail signal
  - Published architecture document artifact
channels:
  - Process exit codes
  - Build artifact storage
---

A CI runner can execute `archledger check` to validate record integrity and `archledger build` to produce the rendered document. Non-zero exit codes signal validation failures. The built Markdown can be published as a CI artifact or deployed to a documentation site.
