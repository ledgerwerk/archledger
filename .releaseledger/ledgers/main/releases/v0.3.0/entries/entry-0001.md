---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 2
entry_id: entry-0001
release_version: v0.3.0
kind: added
summary:
  Added the sdd profile and SDD lifecycle commands enforcing traceability and
  automation policy
status: accepted
audience: null
scopes: []
source_refs:
  - git:af0af85a8233a4ac5baa78fc2db55ddaf1b61b65
  - git:dc89d08b6cb677772b0bbc310a60616cd7ae7ca9
paths:
  - archledger/sdd.py
  - archledger/profiles.py
  - archledger/context.py
  - archledger/mutations.py
  - archledger/links.py
  - archledger/jsonschemas.py
  - archledger/installers.py
  - archledger/cli.py
  - archledger/schemas/archledger.sdd.v1.schema.json
  - archledger/schemas/archledger.sdd-pr.v1.schema.json
  - archledger/schemas/archledger.sdd-status.v1.schema.json
issues: []
prs: []
sources:
  - git:af0af85a8233a4ac5baa78fc2db55ddaf1b61b65
  - git:dc89d08b6cb677772b0bbc310a60616cd7ae7ca9
breaking: false
internal: false
order: 1
---

The same foundation introduces project profiles selected via init --profile and switched with profile enable and profile migrate, compact agent context packs focused on a file or record set, safe record mutation commands (record set, refs add, links add, ac add) that re-run validation, JSON Schema export, and optional install scaffolds for GitHub Actions and agent instructions.
