---
id: quality_scenario_0002
type: quality_scenario
title: "Agent can create and validate records via CLI"
status: accepted
section: quality_requirements
order: 20
quality: "usability"
source: "Coding Agent"
stimulus: "Agent creates a new black-box record and validates it via check --json"
environment: "normal_development"
artifact: "archledger CLI"
response: "CLI returns structured JSON with ok=true, the record ID, and its path"
response_measure: "Zero human interventions required; all operations complete via CLI invocations with exit code 0"
---

Coding agents must be able to create, inspect, and validate architecture records without human intervention. The --json flag provides structured output for all commands. Exit codes distinguish success (0) from failure (1).
