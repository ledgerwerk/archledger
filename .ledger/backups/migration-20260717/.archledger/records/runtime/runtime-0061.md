---
id: runtime-0061
type: runtime_scenario
title: Build multi-format output
schema_version: 4
body_format: markdown
status: accepted
section: runtime_view
order: 40
participants:
  - CLI Layer
  - Render Layer
  - Assembly Layer
  - Converter Layer
trigger:
  User invokes archledger build with optional --format, --formats, --all, or
  --output
result:
  Assembled architecture document in the requested format(s) written to the
  build directory.
source_refs:
  - archledger/cli.py
  - tests/test_repository_cli.py
kind: runtime
version: 1
---

1. CLI resolves the project config and constructs a Repository.
2. Render layer resolves requested output formats from CLI options and config defaults via the formats module.
3. Assembly layer runs check to validate records, then loads all visible records, selects the dialect matching the source format, and renders the document using the appropriate Jinja2 template.
4. Assembly layer writes the native-format assembled document to the build directory.
5. Converter layer computes a conversion plan for each requested non-native format.
6. For native format: file copy. For pandoc-based: invoke pandoc with the appropriate input/output format. For asciidoctor-based: invoke asciidoctor or asciidoctor-pdf directly, or via DocBook intermediate.
7. Results are reported as JSON or human-readable output.
