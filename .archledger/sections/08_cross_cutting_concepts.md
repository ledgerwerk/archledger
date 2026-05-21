---
id: section_cross_cutting_concepts
type: section
section: cross_cutting_concepts
title: Cross-cutting Concepts
order: 80
status: accepted
---

Three cross-cutting concepts pervade the architecture: the record lifecycle (draft, proposed, accepted, deprecated, superseded) which controls visibility and validation behavior, the config discovery mechanism which resolves project paths from the workspace directory upward, and the dialect abstraction which ensures format-neutral rendering for both Markdown and AsciiDoc sources.
