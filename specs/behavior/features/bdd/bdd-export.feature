@area-bdd @feature-bdd-export
Feature: BDD export generates Gherkin feature files from records

  The exporter renders deterministic Gherkin from BDD metadata, with
  path safety checks and overwrite protection.

  @rule-export-single
  Rule: Single record export produces a valid feature file

    @bdd-export-creates-file
    Example: Record with valid BDD metadata exports a feature file
      Given an initialized archledger project with a record containing valid bdd metadata
      When bdd export is called with a relative output path
      Then the feature file is written to the workspace
      And the file contains a generated-header comment
      And the file contains Feature, Scenario, and step lines

    @bdd-export-refuses-no-bdd
    Example: Record without BDD metadata cannot be exported
      Given an initialized archledger project with a record lacking bdd metadata
      When bdd export is called
      Then a ValueError is raised

    @bdd-export-deterministic
    Example: Export is deterministic for the same record
      Given a record with valid bdd metadata
      When export is called twice
      Then both outputs are identical

  @rule-export-safety
  Rule: Export enforces path and overwrite safety

    @bdd-export-refuses-absolute
    Example: Absolute output path is refused
      Given an initialized archledger project
      When bdd export is called with an absolute output path
      Then a validation error is raised before any file is written

    @bdd-export-refuses-overwrite
    Example: Existing file is refused without force
      Given an existing file at the output path
      When bdd export is called without force
      Then a ValueError is raised

  @rule-export-batch
  Rule: Batch export groups by feature and rule

    @bdd-export-all-multi-rule
    Example: Multiple rules are preserved in one feature file
      Given multiple records sharing a feature name but with different rules
      When bdd export all is called
      Then the output feature file contains multiple Rule blocks

  @rule-export-filename
  Rule: Feature filenames are sanitized

    @bdd-export-safe-filename
    Example: Unsafe characters in feature names are collapsed
      Given a feature name with spaces and special characters
      When safe_feature_filename is called
      Then the result is a safe lowercase basename with .feature suffix

    @bdd-export-safe-filename-empty
    Example: Empty feature name falls back to a default
      Given an empty feature name
      When safe_feature_filename is called with a fallback
      Then the result uses the fallback value

    @bdd-export-safe-output-file
    Example: Output file outside workspace is refused
      Given a workspace root and an output directory
      When safe_output_file is called with a filename containing path separators
      Then a ValueError is raised
