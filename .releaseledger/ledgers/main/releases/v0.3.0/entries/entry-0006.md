---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 2
entry_id: entry-0006
release_version: v0.3.0
kind: fixed
summary:
  Fixed renumber and doctor to handle numbering-format changes and ID format
  drift
status: accepted
audience: null
scopes: []
source_refs:
  - git:f27c9058137b5aec0bdc7f8930067297df8fdf2c
  - git:a964a822687d76a49c52d192bc5901935cef074f
paths:
  - archledger/id_format_drift.py
  - archledger/renumber.py
  - archledger/cli.py
  - archledger/repository.py
  - tests/test_renumber_cli.py
issues: []
prs: []
sources:
  - git:f27c9058137b5aec0bdc7f8930067297df8fdf2c
  - git:a964a822687d76a49c52d192bc5901935cef074f
breaking: false
internal: false
order: 6
---
