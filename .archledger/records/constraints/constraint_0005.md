---
id: constraint_0005
type: constraint
title: "No external database dependency"
status: accepted
section: architecture_constraints
order: 50
category: technical
impact: "Storage is limited to the local filesystem. No server process, database engine, or cloud service is required."
---

archledger stores all state as flat files on the local filesystem. The configuration is a TOML file at the project root, records are Markdown files in subdirectories, and metadata is a YAML file. This keeps the dependency footprint small (Typer, PyYAML, Jinja2) and avoids operational complexity.
