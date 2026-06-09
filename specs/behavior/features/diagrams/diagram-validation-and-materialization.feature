@area-diagrams @feature-diagram-validation-and-materialization
Feature: Diagram validation and materialization

  # Diagram records support text-first source readability while preserving
  # Mermaid conversion support when explicitly requested. Validation must be
  # dialect-specific and materialized assets must be deterministic.

  @rule-dialect-blocks
  Rule: Diagram validation uses the source dialect and diagram type

    @bdd-diagram-markdown-mermaid-block-required
    Example: Markdown Mermaid diagram requires a fenced mermaid block
      Given a markdown workspace with an accepted mermaid diagram record
      And the diagram body has no fenced mermaid block
      When archledger check is run
      Then a warning reports the missing markdown mermaid block

    @bdd-diagram-asciidoc-mermaid-block-required
    Example: AsciiDoc Mermaid diagram requires a mermaid literal block
      Given an asciidoc workspace with an accepted mermaid diagram record
      And the diagram body has no mermaid literal block
      When archledger check is run
      Then a warning reports the missing asciidoc mermaid block

    @bdd-diagram-empty-mermaid-block-warns
    Example: Empty Mermaid block is rejected as incomplete
      Given a mermaid diagram record with an empty mermaid block
      When archledger check is run
      Then a warning reports that the mermaid block is empty

  @rule-text-diagrams
  Rule: Text diagrams are default and validate readable source blocks

    @bdd-diagram-new-defaults-to-text
    Example: New diagram defaults to text type
      Given an initialized workspace
      When archledger new diagram is run without a diagram type
      Then the created record metadata has diagram_type text

    @bdd-diagram-configured-default-type
    Example: Configured diagram default type is honored
      Given the config sets the default diagram type to unicode
      When archledger new diagram is run without a diagram type
      Then the created record metadata has diagram_type unicode

    @bdd-diagram-markdown-text-block-accepted
    Example: Markdown textdiagram block is accepted
      Given a markdown diagram record with a non-empty textdiagram block
      When archledger check is run
      Then no diagram block warning is reported

    @bdd-diagram-asciidoc-source-block-accepted
    Example: AsciiDoc source block is accepted for text diagrams
      Given an asciidoc diagram record with a non-empty source block
      When archledger check is run
      Then no diagram block warning is reported

    @bdd-diagram-empty-text-block-warns
    Example: Empty textdiagram block warns
      Given a text diagram record with an empty diagram block
      When archledger check is run
      Then a warning reports that the text diagram block is empty

    @bdd-diagram-overwide-text-line-warns
    Example: Overwide textdiagram line warns
      Given a text diagram block containing a line wider than 120 characters
      When archledger check is run
      Then a warning reports the overwide text diagram line

  @rule-materialization
  Rule: Diagram materialization is deterministic and explicit about renderer failure

    @bdd-diagram-materialize-markdown-mermaid
    Example: Markdown Mermaid block is rewritten to an image reference
      Given a markdown assembly result containing a mermaid block
      When diagrams are materialized for conversion
      Then the body references a generated image asset
      And the original mermaid source is preserved for hashing

    @bdd-diagram-materialize-asciidoc-mermaid
    Example: AsciiDoc Mermaid block is rewritten to an image reference
      Given an asciidoc assembly result containing a mermaid block
      When diagrams are materialized for conversion
      Then the body references a generated image asset

    @bdd-diagram-asset-name-content-hash
    Example: Diagram asset names are content-hash deterministic
      Given two identical mermaid diagram blocks
      When diagrams are materialized for conversion
      Then both assets use the same deterministic content hash name

    @bdd-diagram-mermaid-missing-actionable-error
    Example: Missing mermaid-cli produces actionable renderer error
      Given mermaid-cli is configured as renderer
      And mermaid-cli is not available on PATH
      When diagrams are materialized for conversion
      Then rendering fails with an actionable installation error

    @bdd-diagram-mermaid-still-supported
    Example: Mermaid remains supported when requested
      Given a diagram record explicitly marked as mermaid
      When archledger check is run against a valid mermaid block
      Then no diagram type warning is reported
