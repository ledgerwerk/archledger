---
id: constraint_0004
type: constraint
title: "Python 3.10+ runtime"
status: accepted
section: architecture_constraints
order: 40
category: technical
impact: "All user-facing functionality is exposed through Typer CLI commands. No GUI, no web API."
---

archledger requires Python >= 3.10, as declared in `pyproject.toml`. This allows the use of modern type hint syntax (`X | Y` unions, `match` statements) while still supporting current Python distributions on Linux and macOS.
