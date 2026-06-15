---
id: quality-0016
type: quality_goal
title: Reproducibility
schema_version: 4
body_format: markdown
status: accepted
section: introduction_and_goals
order: 20
priority: 1
scenario:
  Given the same set of accepted records, archledger build produces byte-identical
  output regardless of the host machine or locale.
source_refs:
  - tests/test_build.py
  - tests/test_source_tracking.py
kind: quality
version: 1
---

Builds are deterministic: the same records always produce byte-identical output. The document date is deterministic (`SOURCE_DATE_EPOCH` when set, otherwise the maximum accepted-record metadata date), sort orders are explicit, and no randomness or network access is involved during rendering. This supports reproducible documentation pipelines.
