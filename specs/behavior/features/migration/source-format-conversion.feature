@area-migration @feature-source-format-conversion
Feature: Source format conversion

  # Source format conversion is a deliberate write operation. It should preserve
  # modern configuration, require Pandoc for real conversion unless mixed bodies
  # are allowed, and remove replaced source files only in replace mode.

  @rule-write-safety
  Rule: Conversion requires explicit write for mutation

    @bdd-convert-requires-write
    @req-REQ-0009
    @ac-AC-0089
    Example: Conversion without write only plans changes
      Given a workspace with markdown records
      When source conversion is requested without write
      Then no record files are modified
      And the result reports a conversion plan

  @rule-tool-requirements
  Rule: Conversion requires Pandoc unless mixed body format is allowed

    @bdd-convert-write-requires-pandoc
    @req-REQ-0009
    @ac-AC-0090
    Example: Write conversion fails when Pandoc is missing
      Given a workspace with records requiring body conversion
      And pandoc is not available on PATH
      When source conversion is requested with write
      Then the command fails with a missing Pandoc error

    @bdd-convert-allow-mixed-without-pandoc
    @req-REQ-0009
    @ac-AC-0091
    Example: Mixed body format can bypass Pandoc
      Given a workspace with records in another body format
      And mixed body format is allowed
      When source conversion is requested with write
      Then record metadata is updated without requiring Pandoc

    @bdd-convert-uses-pandoc-when-available
    @req-REQ-0009
    @ac-AC-0092
    Example: Pandoc is used for body conversion when available
      Given pandoc is available on PATH
      When source conversion is requested with write
      Then pandoc is invoked for convertible record bodies

  @rule-config-preservation
  Rule: Conversion preserves current config and optional replacement behavior

    @bdd-convert-preserves-v5-config
    @req-REQ-0009
    @ac-AC-0093
    Example: Conversion preserves tracking and build config
      Given a v5 config with tracking and build settings
      When source conversion is performed
      Then the converted config retains those settings

    @bdd-convert-replace-removes-old-files
    @req-REQ-0009
    @ac-AC-0094
    Example: Replace mode removes old source files
      Given a workspace with markdown source files
      When conversion to asciidoc is run with replace mode
      Then converted asciidoc files are written
      And the old markdown files are removed
