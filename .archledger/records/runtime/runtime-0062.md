---
id: runtime-0062
type: runtime_scenario
title: Detect changed files and impacted records
schema_version: 2
date: "2026-05-21"
body_format: markdown
status: accepted
section: runtime_view
order: 50
participants:
  - CLI Layer
  - Source Tracking Layer
  - Repository Layer
trigger: User invokes archledger source changed
result:
  List of changed files, impacted architecture records, impacted sections, and
  unlinked changed files.
source_refs:
  - archledger/cli.py
  - tests/test_repository_cli.py
kind: runtime
---

1. CLI loads the tracking baseline from the source state JSON file (if it exists).
2. Source tracking scans the current workspace, computing SHA-256 hashes for all tracked files.
3. Source tracking diffs the baseline against the current state to produce a ChangeSet (added, modified, deleted files, possible renames).
4. Repository loads all architecture records (including sections).
5. Source tracking resolves impacts by matching changed file paths against record `source_refs`.
6. Results include: impacted records (with matched refs), impacted sections, and unlinked changed files.
7. If no baseline exists, all files are reported as unbaselined.
