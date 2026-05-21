---
id: quality_goal_0001
type: quality_goal
title: "Maintainability"
status: accepted
section: introduction_and_goals
order: 10
priority: 1
scenario: "A developer can add a new record type with template, model mapping, and CLI alias in under 30 minutes, touching at most three files."
---

Each arc42 record type corresponds to a small, self-contained unit. Adding or changing a record type requires modifying only the model mapping, the Jinja2 template, and optionally the CLI alias table. The codebase avoids deep inheritance or framework coupling so that contributors can understand the data flow quickly.
