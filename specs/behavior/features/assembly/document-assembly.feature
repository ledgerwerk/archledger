@area-assembly @feature-document-assembly
Feature: Document assembly

  The assembly command renders all records into a single arc42 document
  in the configured output format.

  @rule-assembly
  Rule: Assembly produces a complete arc42 document

    @bdd-assembly-creates-output
    @req-REQ-0001
    @ac-AC-0016
    Example: Assembly writes an output file
      Given a workspace with accepted records
      When assemble_document is run
      Then an output file is created

    @bdd-assembly-includes-all-sections
    @req-REQ-0001
    @ac-AC-0017
    Example: Assembly includes all 12 arc42 major sections
      Given a workspace with records in multiple sections
      When assemble_document is run
      Then the output contains section headings for all 12 sections

    @bdd-assembly-includes-drafts
    @req-REQ-0001
    @ac-AC-0018
    Example: Assembly includes draft records when flag is set
      Given a workspace with draft records
      When assemble_document is run with include_draft True
      Then draft records appear in the output

    @bdd-assembly-excludes-drafts
    @req-REQ-0001
    @ac-AC-0019
    Example: Assembly excludes draft records by default
      Given a workspace with only draft records
      When assemble_document is run
      Then no draft records appear in the output

    @bdd-assembly-includes-superseded
    @req-REQ-0001
    @ac-AC-0020
    Example: Assembly includes superseded records when flag is set
      Given a workspace with superseded records
      When assemble_document is run with include_superseded True
      Then superseded records appear in the output

    @bdd-assembly-schema
    @req-REQ-0001
    @ac-AC-0021
    Example: Assembly result includes source format
      Given a markdown workspace
      When assemble_document is run
      Then the result source_format is "markdown"

  @rule-formats
  Rule: Assembly supports multiple output formats

    @bdd-assembly-format-from-extension
    @req-REQ-0001
    @ac-AC-0022
    Example: Output format is inferred from file extension
      Given a workspace and output path "doc.html"
      When assemble_document is run
      Then the output format is "html"

    @bdd-assembly-format-markdown
    @req-REQ-0001
    @ac-AC-0023
    Example: Markdown source produces markdown output
      Given a markdown workspace
      When assemble_document is run with no explicit format
      Then the output is markdown
