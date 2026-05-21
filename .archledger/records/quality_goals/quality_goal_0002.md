---
id: quality_goal_0002
type: quality_goal
title: "Reproducibility"
status: accepted
section: introduction_and_goals
order: 20
priority: 1
scenario: "Given the same set of accepted records, archledger build produces byte-identical output regardless of the host machine or locale."
---

Builds are deterministic: the same records always produce the same Markdown document. Timestamps are controlled, sort orders are explicit, and no randomness or network access is involved during rendering. This supports reproducible documentation pipelines.
