---
id: black_box_0009
type: black_box
title: "Converter Layer"
status: accepted
section: building_block_view
level: 1
parent: white_box_0001
order: 80
interfaces:
  - convert_assembled_document()
location:
  - archledger/converters.py
  - archledger/formats.py
fulfilled_requirements: []
risks: []
tags: []
created_at: "2026-05-20T12:00:00Z"
updated_at: "2026-05-20T12:00:00Z"
---

The converter module handles multi-format export. It takes an assembled document (from the Assembly Layer) and produces output in the requested formats. For native format builds (Markdown source to Markdown output, or AsciiDoc source to AsciiDoc output), it does a direct file copy. For other formats, it invokes external converters: pandoc for Markdown-to-HTML/PDF/DOCX/RST/Textile, asciidoctor for AsciiDoc-to-HTML/PDF (direct or via DocBook intermediate), and pandoc for AsciiDoc-to-DOCX/Markdown/RST/Textile (via DocBook). The formats module (`formats.py`) defines the `OutputFormat` enum and resolves requested formats from CLI options and config.

Conversion plans are computed per format: native copy, direct converter invocation, or DocBook intermediate. DocBook intermediates are cleaned up unless `build_keep_intermediate` is set.
