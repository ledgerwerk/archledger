---
id: content-0003
type: section
section: context_and_scope
title: Context and Scope
schema_version: 2
date: "2026-05-21"
body_format: markdown
order: 30
status: accepted
kind: content
---

archledger interacts with three external partners: the source repository (reads config and records, writes build output), coding agents (CLI invocations with JSON output), and CI pipelines (exit codes and build artifacts). Optional external converters (pandoc, asciidoctor, asciidoctor-pdf) are invoked as subprocesses for multi-format exports. All communication is local filesystem access, process I/O, or subprocess invocation.

See the [System Context diagram](#diagram-al_diagram_0035) for a visual overview of actors and system boundaries.
