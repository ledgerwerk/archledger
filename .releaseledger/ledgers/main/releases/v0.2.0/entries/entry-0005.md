---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 2
entry_id: entry-0005
release_version: v0.2.0
kind: changed
summary:
  Changed default build output location and limited diagram renderers to three
  supported options
status: accepted
audience: null
scopes: []
source_refs:
  - git:bbef02d1255d769d5ae369457ad668f477f30a3b
paths:
  - archledger/cli_options.py
  - archledger/ledger_sequence.py
  - archledger/config/schema.py
  - archledger/repository_checks.py
  - archledger/diagrams.py
  - archledger/templates/records/_frontmatter.j2
  - tests/test_refactoring_regression.py
issues: []
prs: []
sources:
  - git:bbef02d1255d769d5ae369457ad668f477f30a3b
breaking: false
internal: false
order: 5
---
