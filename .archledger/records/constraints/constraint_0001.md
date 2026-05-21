---
id: constraint_0001
type: constraint
title: "Typer CLI interface"
status: accepted
section: architecture_constraints
order: 10
category: technical
impact: "All user-facing functionality is exposed through Typer CLI commands. No GUI, no web API, no library-first API."
---

archledger uses Typer as its CLI framework. The entry point is `archledger.launcher:main`, registered as the `archledger` console script. All commands return either human-readable text or `--json` structured output. This constraint keeps the tool focused on CLI and automation workflows.
