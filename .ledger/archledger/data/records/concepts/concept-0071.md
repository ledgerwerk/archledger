---
id: concept-0071
type: concept
title: Record lifecycle and status
schema_version: 4
body_format: markdown
status: accepted
section: cross_cutting_concepts
order: 10
applies_to:
  - Repository Layer
  - CLI Layer
  - Record Mutation Service
source_refs:
  - README.md
  - archledger/section_rendering.py
  - archledger/repository.py
  - archledger/mutations.py
kind: concept
version: 2
---

Every live record has a status: `draft`, `proposed`, `accepted`, `deprecated`, or
`superseded`. Status controls default visibility in reads and builds. Draft and
incomplete live records produce validation findings; explicit include options
can expose hidden lifecycle states.

Archiving is separate from status. `archledger archive` moves an obsolete record
to the archive, preserves its ledger number, and leaves a tombstone so identity
is never reused. Archived records are historical evidence and are not mutated to
silence live-content warnings.

All supported live-record mutations increment the version once when content
changes. No-op complete-document apply preserves the version, and failed target
validation restores the original text.
