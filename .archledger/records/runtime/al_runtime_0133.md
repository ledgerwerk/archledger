---
schema_version: 2
id: al_runtime_0133
type: runtime_scenario
title: Agent implements after approval
status: proposed
section: runtime_view
order: 160
date: "2026-06-07"
participants: []
trigger: ""
result: ""
body_format: markdown
created_at: "2026-06-07T06:45:33Z"
updated_at: "2026-06-07T06:45:33Z"
bdd:
  feature: Task lifecycle gates
  scenario: Agent implements after approval
  tags:
    - lifecycle
    - approval
  given:
    - a task has an approved plan
  when:
    - the agent starts implementation
  then:
    - implementation proceeds normally
  automation:
    status: pending
  rule: Implementation requires an accepted plan
source_refs:
  - path: tests/fixtures/bdd/lifecycle.feature
    role: documents
    reason: Imported Gherkin scenario source.
---

Describe the runtime scenario.

## Scenario

Rule: Implementation requires an accepted plan

Example: Agent implements after approval

Given a task has an approved plan
When the agent starts implementation
Then implementation proceeds normally
