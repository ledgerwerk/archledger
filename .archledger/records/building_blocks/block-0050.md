---
id: block-0050
type: black_box
title: Converter Layer
schema_version: 2
date: "2026-05-20"
body_format: markdown
status: accepted
section: building_block_view
level: 1
parent: block-0041
order: 80
interfaces:
  - convert_assembled_document()
location:
  - archledger/converters.py
  - archledger/conversion_plan.py
  - archledger/formats.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T12:00:00Z"
updated_at: "2026-05-20T12:00:00Z"
source_refs:
  - archledger/converters.py
  - archledger/conversion_plan.py
  - archledger/formats.py
kind: block
---

The converter module handles multi-format export. It takes an assembled document (from the Assembly Layer) and produces output in the requested formats. For native format builds (Markdown source to Markdown output, or AsciiDoc source to AsciiDoc output), it does a direct file copy. For other formats, it invokes external converters: pandoc for Markdown-to-HTML/PDF/DOCX/RST/Textile, asciidoctor for AsciiDoc-to-HTML/PDF (direct or via DocBook intermediate), and pandoc for AsciiDoc-to-DOCX/Markdown/RST/Textile (via DocBook). The formats module (`formats.py`) defines the `OutputFormat` enum and resolves requested formats from CLI options and config.

Conversion planning is handled by `conversion_plan.py`, which produces a `ConversionPlan` dataclass for each requested format. Each plan specifies whether the conversion is a native copy, a direct tool invocation, or requires a DocBook intermediate step. Tool resolution uses `shutil.which` by default. The `require_tool()` function raises `RenderError` with install hints when a required converter is unavailable. DocBook intermediates are cleaned up unless `build_keep_intermediate` is set.
