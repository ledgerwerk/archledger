---
schema_version: 4
id: block-0139
type: black_box
title: Specification and traceability services
status: proposed
section: building_block_view
level: 1
parent: block-0041
order: 175
interfaces: []
location: []
fulfilled_requirements:
  - content-0136
  - content-0137
  - content-0138
risks: []
tags: []
body_format: markdown
source_refs:
  - path: archledger/sdd.py
    role: implements
    reason: SDD policy evaluation service.
  - path: archledger/context.py
    role: implements
    reason: Focused context selection service.
  - path: archledger/trace.py
    role: implements
    reason: Record relationship traversal service.
  - path: archledger/bdd/
    role: implements
    reason: BDD parsing and artifact exchange subsystem.
  - path: archledger/mutations.py
    role: implements
    reason: Safe record mutation operations used by specification workflows.
kind: block
version: 1
---

This logical subsystem turns architecture records into enforceable,
agent-consumable specifications.

- **SDD policy evaluator** checks accepted requirements, ADRs, quality
  scenarios, references, validation evidence, waivers, and BDD metadata.
- **Context service** selects bounded record sets from a file, record, or source
  drift query.
- **Trace service** traverses links and evidence around a record.
- **BDD service** parses a constrained Gherkin subset, imports or exports
  behavior metadata, links SpecWeave-owned feature files through `source_refs`,
  links plain pytest enforcement through `test_refs`, and never executes test
  runners.
- **Mutation service** updates status, metadata, bodies, links, references, and
  acceptance criteria while reusing repository validation.

The CLI layer owns presentation and command gating; these services own the
domain behavior and return structured payloads.
