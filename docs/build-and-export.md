# Build and export

## Native builds

```{code-block} bash
archledger build --format markdown
archledger build --format asciidoc
```

`[build].default_output_dir` is relative to the directory containing
`archledger.toml` or `.archledger.toml`. New projects default to `build/`
under the workspace root, and projects may override this path.

## Converter-backed exports

- Markdown source uses `pandoc` for HTML, DOCX, RST, Textile, PDF, and AsciiDoc.
- AsciiDoc source uses `asciidoctor` for HTML.
- AsciiDoc source uses `asciidoctor-pdf` for PDF.
- AsciiDoc source uses Asciidoctor DocBook plus `pandoc` for DOCX, Markdown, RST, and Textile.

These export paths are supported when the external tools are installed and the
corresponding integration checks pass. Native Markdown and AsciiDoc assembly
remain the lowest-friction path because they do not depend on external converters.

## Diagram records

Diagram records are plain text by default. Dense architecture diagrams should use
`diagram_type = "text"` or `"unicode"` so they remain readable in source,
Git diffs, terminal output, and native Markdown/AsciiDoc builds. Mermaid remains
available for compact sequence or flow diagrams, but it is not the default.

Supported `diagram_type` values: `text` (default), `ascii`, `unicode`,
`svgbob`, `mermaid`.

Native builds preserve text diagram blocks as readable fenced code blocks or
literal blocks — no external tool is required.

Optional materialization for converter-backed outputs can be enabled with:

```{code-block} toml
[diagrams]
enabled = true
renderer = "mermaid-cli"
default_type = "text"
output_dir = "diagrams"
image_format = "svg"
kroki_url = ""
```

Notes:

- `renderer = "pass-through"` keeps diagram blocks unchanged (default).
- `renderer = "mermaid-cli"` requires `mmdc` on `PATH` and only processes Mermaid blocks.
- `renderer = "asciidoctor-diagram"` is intended for direct Asciidoctor flows.
- Kroki is not currently supported by config validation.

## Source migration

`source convert` migrates Markdown-source projects to AsciiDoc-source projects.
Write mode is strict by default and requires `pandoc`:

```{code-block} bash
archledger source convert --to asciidoc --apply
```

For an explicit temporary mixed-body migration:

```{code-block} bash
archledger source convert --to asciidoc --apply --allow-mixed-body-format
```
