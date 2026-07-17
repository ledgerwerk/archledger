---
id: content-0003
type: section
section: context_and_scope
title: Context and Scope
schema_version: 4
body_format: markdown
order: 30
status: accepted
kind: content
version: 2
---

Archledger interacts with the source repository, developers and coding agents,
CI pipelines, and optional document converters. All communication uses local
filesystem access, process I/O, or converter subprocesses. The CLI returns human
text or stable JSON envelopes for automation.

Behavior specifications and other ledgers are external systems. Archledger may
preserve opaque links or source references to their artifacts, but it does not
execute their workflows or interpret cross-ledger semantics. SpecMason owns the
repository's behavior specifications.

See the [System Context diagram](#diagram-al_diagram_0035) for a visual overview
of actors and system boundaries.
