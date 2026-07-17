---
schema_version: 4
id: block-0141
kind: block
type: black_box
title: Record Mutation Service
status: accepted
section: building_block_view
level: 1
parent: block-0041
order: 175
version: 2
interfaces:
  - export_record_document()
  - apply_record_document()
  - set_record_meta()
  - replace_record_body()
  - add_source_ref()
  - add_test_ref()
  - add_link()
  - add_acceptance_criterion()
location:
  - archledger/mutations.py
  - archledger/storage/frontmatter.py
fulfilled_requirements:
  - content-0017
risks: []
tags:
  - mutation
  - source-first
body_format: markdown
source_refs:
  - path: archledger/mutations.py
    role: implements
    reason: Provides versioned record mutation operations.
  - path: archledger/cli.py
    role: implements
    reason:
      Exposes record, refs, links, and acceptance-criterion mutation commands
      with rollback.
  - path: archledger/storage/frontmatter.py
    role: implements
    reason: Parses and writes complete front-matter documents.
test_refs:
  - tests/test_mutation_cli.py
---

The Record Mutation Service provides the supported write path for existing
architecture records. It updates status, typed metadata, bodies, source and test
references, links, and inline acceptance criteria while preserving record
identity and incrementing the record version once per logical mutation.

`record export` emits a complete editable record document. `record apply`
validates the candidate identity and kind, ignores a caller-supplied version,
and increments from the stored version only when content changed. CLI mutation
commands snapshot the original text, run repository validation after the write,
and restore the original record if the target becomes invalid.

The service owns mutation mechanics only. Repository validation owns record and
cross-reference rules, while the CLI owns argument parsing, typed value input,
and human or JSON presentation.
