---
id: constraint_0002
type: constraint
title: "Markdown or AsciiDoc with YAML front matter as canonical source"
status: accepted
section: architecture_constraints
order: 20
category: technical
impact: "Record files are plain text, diffable in version control, and editable without special tooling. Both Markdown and AsciiDoc are supported as first-class source formats."
---

Every architecture record is stored as a Markdown or AsciiDoc file with YAML front matter delimited by `---`. The front matter holds machine-readable metadata and the body holds human-readable prose in the configured dialect. No database, binary format, or JSON store is used. The `body_format` field in each record must match the project's configured `source.format`.
