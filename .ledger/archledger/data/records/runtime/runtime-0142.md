---
schema_version: 4
id: runtime-0142
kind: runtime
type: runtime_scenario
title: Safely replace an architecture record
status: accepted
section: runtime_view
order: 70
version: 2
participants:
  - CLI Layer
  - Record Mutation Service
  - Repository Layer
  - Storage Layer
trigger:
  A user exports a record, edits the complete document, and invokes archledger
  record apply.
result:
  A valid changed document is stored with one version increment, or the original
  document is restored on validation failure.
body_format: markdown
source_refs:
  - path: archledger/cli.py
    role: implements
    reason: Coordinates export, apply, target validation, and rollback.
  - path: archledger/mutations.py
    role: implements
    reason: Applies identity-preserving complete-document replacement.
test_refs:
  - tests/test_mutation_cli.py
---

1. The user invokes `archledger record export RECORD_ID --output FILE`.
2. The CLI resolves the record and the mutation service verifies its identity
   before exporting the complete front-matter document.
3. The user edits metadata and body content in the exported file.
4. The user invokes `archledger record apply RECORD_ID --from-file FILE`.
5. The mutation service parses the candidate, verifies that ID and kind match
   the stored record, and compares normalized metadata and body content.
6. If unchanged, the command reports no change and preserves the version.
7. If changed, the service writes the candidate with exactly one version
   increment, regardless of the version supplied in the candidate.
8. The Repository checks the resulting target record and relevant contracts.
9. On validation failure, the CLI atomically restores the original text and
   returns an error. Otherwise it reports the applied change.
