---
id: quality_goal_0003
type: quality_goal
title: "Traceability"
status: accepted
section: introduction_and_goals
order: 30
priority: 1
scenario: "Every architecture record links to source evidence (file paths, CLI commands, test names) so that a reviewer can trace any documented decision back to code within two clicks."
---

Each record carries a machine-readable YAML front matter with fields for source references, parent IDs, and related ADRs. The check command validates that all cross-references resolve. This makes it possible to navigate the architecture document both top-down (from goals to building blocks) and bottom-up (from source files to architectural decisions).
