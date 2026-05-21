---
id: section_context_and_scope
type: section
section: context_and_scope
title: Context and Scope
order: 30
status: accepted
---

archledger interacts with three external partners: the source repository (reads config and records, writes build output), coding agents (CLI invocations with JSON output), and CI pipelines (exit codes and build artifacts). Optional external converters (pandoc, asciidoctor, asciidoctor-pdf) are invoked as subprocesses for multi-format exports. All communication is local filesystem access, process I/O, or subprocess invocation.
