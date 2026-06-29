@area-records @feature-model-constants
Feature: Model constants and format specs

  The model module defines constants for source formats, output formats,
  statuses, sections, and format specifications.

  @rule-source-formats
  Rule: Source formats are markdown and asciidoc

    @bdd-model-valid-source-formats
    @req-REQ-0012
    @ac-AC-0101
    Example: Valid source formats include markdown and asciidoc
      Given the VALID_SOURCE_FORMATS set
      When checked
      Then it contains "markdown" and "asciidoc"

    @bdd-model-source-format-extensions
    @req-REQ-0012
    @ac-AC-0102
    Example: Source format extensions map correctly
      Given the SOURCE_FORMAT_EXTENSIONS mapping
      When "markdown" is looked up
      Then the extension is ".md"

  @rule-output-formats
  Rule: Output formats include html, pdf, docx, and others

    @bdd-model-valid-output-formats
    @req-REQ-0012
    @ac-AC-0103
    Example: Valid output formats include html, pdf, docx, markdown
      Given the VALID_OUTPUT_FORMATS set
      When checked
      Then it contains "html", "pdf", "docx", "markdown"

  @rule-statuses
  Rule: Record statuses define lifecycle states

    @bdd-model-valid-statuses
    @req-REQ-0012
    @ac-AC-0104
    Example: Valid statuses include draft, proposed, accepted, deprecated
      Given the VALID_STATUSES set
      When checked
      Then it contains "draft", "proposed", "accepted", "deprecated"

    @bdd-model-visible-by-default
    @req-REQ-0012
    @ac-AC-0105
    Example: Visible by default statuses are proposed, accepted, deprecated
      Given the VISIBLE_BY_DEFAULT_STATUSES set
      When checked
      Then it contains "proposed", "accepted", "deprecated"

  @rule-sections
  Rule: Sections define the arc42 document structure

    @bdd-model-section-order
    @req-REQ-0012
    @ac-AC-0106
    Example: Section order maps all 12 arc42 sections
      Given the SECTION_ORDER mapping
      When checked
      Then it contains 12 entries from introduction_and_goals to glossary

    @bdd-model-major-section-specs
    @req-REQ-0012
    @ac-AC-0107
    Example: Major section specs define all 12 sections
      Given the MAJOR_SECTION_SPECS tuple
      When checked
      Then it contains 12 SectionSpec instances
