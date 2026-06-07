---
schema_version: 2
id: al_runtime_0128
type: runtime_scenario
title: Agent tries to implement before approval
status: proposed
section: runtime_view
order: 110
date: "2026-06-07"
participants: []
trigger: ""
result: ""
body_format: markdown
created_at: "2026-06-07T06:43:39Z"
updated_at: "2026-06-07T06:43:39Z"
bdd:
  feature: Task lifecycle gates
  scenario: Agent tries to implement before approval
  tags:
    - lifecycle
    - approval
    - happy-path
  given:
    - a task has a proposed plan
    - the plan has not been approved by the user
  when:
    - the agent starts implementation
  then:
    - implementation is blocked
    - the task remains in planning or review state
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

Example: Agent tries to implement before approval

Given a task has a proposed plan
Given the plan has not been approved by the user
When the agent starts implementation
Then implementation is blocked
And the task remains in planning or review state
