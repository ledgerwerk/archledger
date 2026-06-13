---
schema_version: 2
id: runtime-0131
type: runtime_scenario
title: Agent implements after approval
status: proposed
section: runtime_view
order: 140
date: "2026-06-07"
participants: []
trigger: ""
result: ""
body_format: markdown
created_at: "2026-06-07T06:43:46Z"
updated_at: "2026-06-07T06:43:46Z"
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
kind: runtime
---

Describe the runtime scenario.

## Scenario

Rule: Implementation requires an accepted plan

Example: Agent implements after approval

Given a task has an approved plan
When the agent starts implementation
Then implementation proceeds normally
