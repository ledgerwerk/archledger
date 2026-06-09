@area-assembly @feature-build-format-conversion
Feature: Build format conversion and output selection

  # Build output selection must be deterministic, safe, and explicit about
  # required external tools. Native source-format output should not require
  # conversion tools, while tool-backed formats must fail early with actionable
  # errors when a renderer is missing.

  @rule-native-output
  Rule: Native outputs avoid external conversion tools

    @bdd-build-markdown-native-without-tools
    Example: Markdown source builds markdown without external tools
      Given an initialized workspace using markdown source format
      When archledger build is run with format markdown
      Then the markdown output file is written
      And no external converter is required

    @bdd-build-asciidoc-native-without-tools
    Example: AsciiDoc source builds AsciiDoc without external tools
      Given an initialized workspace using asciidoc source format
      When archledger build is run with format asciidoc
      Then the asciidoc output file is written
      And no external converter is required

    @bdd-build-native-uses-configured-output
    Example: Native build uses configured default output
      Given a workspace with build output configured for the native source format
      When assemble_document is run without an explicit output path
      Then the configured output path is used

  @rule-tool-errors
  Rule: Tool-backed formats fail with actionable install hints

    @bdd-build-html-requires-asciidoctor
    Example: HTML output requires asciidoctor
      Given asciidoctor is not available on PATH
      When archledger build is run with format html
      Then the command fails
      And the error explains that asciidoctor was not found

    @bdd-build-pdf-requires-asciidoctor-pdf
    Example: PDF output requires asciidoctor-pdf
      Given asciidoctor-pdf is not available on PATH
      When archledger build is run with format pdf
      Then the command fails
      And the error explains that asciidoctor-pdf was not found

    @bdd-build-docx-requires-pandoc
    Example: DOCX output requires pandoc
      Given asciidoctor is available
      And pandoc is not available on PATH
      When archledger build is run with format docx
      Then the command fails
      And the error explains that pandoc was not found

    @bdd-build-pandoc-format-requires-asciidoctor
    Example: Pandoc-backed output still requires asciidoctor for AsciiDoc source
      Given pandoc is available
      And asciidoctor is not available on PATH
      When archledger build is run with format rst
      Then the command fails
      And the error explains that asciidoctor was not found

  @rule-conversion-pipeline
  Rule: Conversion commands are generated deterministically

    @bdd-build-docbook-intermediate-before-pandoc
    Example: Pandoc-backed formats use DocBook as intermediate
      Given asciidoctor and pandoc are available
      When archledger build is run with format markdown
      Then asciidoctor is invoked to create a DocBook intermediate
      And pandoc is invoked with input format docbook and target format gfm

    @bdd-build-output-extension-infers-format
    Example: Explicit output extension infers requested format
      Given asciidoctor and pandoc are available
      When archledger build is run with output docs/architecture.md
      Then the build result format is markdown
      And the output file is written under docs

    @bdd-build-mermaid-renderer-only-when-enabled
    Example: Mermaid rendering is invoked only when diagram rendering is enabled
      Given a workspace with a mermaid diagram record
      When archledger build is run with diagram rendering disabled
      Then mermaid-cli is not invoked

  @rule-multiple-outputs
  Rule: Multiple output selection obeys config and CLI precedence

    @bdd-build-json-reports-multiple-outputs
    Example: JSON build reports every generated output
      Given html and markdown outputs are requested
      When archledger build is run with JSON output
      Then the result lists both generated output paths

    @bdd-build-default-includes-enabled-outputs
    Example: Default build includes enabled configured outputs
      Given the config has multiple build outputs
      And one output is enabled
      When archledger build is run without explicit formats
      Then the enabled output is generated

    @bdd-build-all-skips-disabled-outputs
    Example: Build all honors disabled configured outputs
      Given the config has one disabled build output
      When archledger build --all is run
      Then the disabled output is not generated

    @bdd-build-explicit-format-overrides-disabled-output
    Example: Explicit format can override a disabled configured output
      Given the config disables markdown output
      When archledger build is run with format markdown
      Then markdown output is still generated

    @bdd-build-rejects-multiple-formats-with-one-file
    Example: Multiple formats cannot share a single output file
      Given two formats are requested
      When archledger build is run with one explicit output file
      Then the command fails before writing output
