---
id: runtime-0058
type: runtime_scenario
title: Validate records with check
schema_version: 4
body_format: markdown
status: accepted
section: runtime_view
order: 20
participants:
  - CLI Layer
  - Repository Layer
  - Storage Layer
trigger: User invokes archledger check or archledger check --strict
result:
  Errors and warnings are reported in human or JSON form; strict mode exits
  non-zero for either category.
source_refs:
  - archledger/cli.py
  - archledger/repository.py
  - archledger/model.py
  - archledger/record_types.py
  - tests/test_repository_cli.py
kind: runtime
version: 2
---

1. The CLI resolves project configuration and constructs the Repository.
2. Storage parses sections and live record files with their configured dialect.
3. Core validation checks required fields, lifecycle values, ID and filename
   consistency, segment expectations, and body format.
4. The Model obtains per-record metadata field specifications from the Record
   Type Registry and validates scalar, list, and object shapes.
5. Repository checks duplicate IDs, parents, links, source and test references,
   and archive invariants.
6. Specialized checks report placeholders and type-specific completeness issues.
7. Normal mode fails on errors. Strict mode also promotes warnings to a failing
   result.
8. The CLI emits the same result through human formatting or a JSON envelope.
