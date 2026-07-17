---
id: content-0011
type: section
section: risks_and_technical_debt
title: Risks and Technical Debt
schema_version: 4
body_format: markdown
order: 110
status: accepted
kind: content
version: 1
---

Primary risks: documentation can drift from implementation (mitigated by source tracking, CI check integration, and `source_refs` on records), counter collisions when the storage metadata becomes stale (mitigated by the --repair-counters flag), and dependency on external converters (pandoc, asciidoctor) for non-native export formats which may not be available in all environments.
