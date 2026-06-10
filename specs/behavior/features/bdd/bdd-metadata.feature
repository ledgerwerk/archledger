@area-bdd @feature-bdd-metadata
Feature: BDD metadata normalization and models

  The normalizer validates the `bdd` front-matter block, producing a
  BddExample when structurally valid and warnings for shape violations.

  @rule-models
  Rule: BDD models are immutable and hashable

    @bdd-models-frozen
    Example: BddExample and BddAutomation are frozen dataclasses
      Given a BddExample with populated fields
      When an attempt is made to reassign a field
      Then an AttributeError is raised
      And the example is hashable via the built-in hash function

    @bdd-models-automation-defaults
    Example: BddAutomation defaults to status pending
      Given a BddAutomation constructed without arguments
      When the automation status and optional fields are read
      Then status is "pending"
      And feature_file, scenario, and command are empty strings

  @rule-normalization
  Rule: Normalization validates structure and types

    @bdd-normalize-complete
    Example: Complete BDD block normalizes without warnings
      Given a complete BDD metadata mapping with all fields
      When normalize_bdd_metadata is called
      Then the returned example has all fields populated correctly
      And the warnings list is empty

    @bdd-normalize-none
    Example: None value returns no example and no warnings
      Given a None bdd value
      When normalize_bdd_metadata is called
      Then the returned example is None
      And the warnings list is empty

    @bdd-normalize-non-mapping
    Example: Non-mapping value returns None with a warning
      Given a bdd value that is a list instead of a mapping
      When normalize_bdd_metadata is called
      Then the returned example is None
      And a warning mentions the value must be a mapping

    @bdd-normalize-missing-required
    Example: Missing required fields produce warnings
      Given a bdd mapping missing feature and scenario
      When normalize_bdd_metadata is called
      Then the example is still returned with empty strings
      And warnings mention missing feature and scenario fields

    @bdd-normalize-wrong-types
    Example: Wrong types for fields produce warnings
      Given a bdd mapping with non-string feature and non-list given
      When normalize_bdd_metadata is called
      Then warnings mention type mismatches
      And sequence entries that are non-string or empty are skipped

  @rule-automation-normalization
  Rule: Automation sub-block is validated independently

    @bdd-normalize-automation-default
    Example: Empty automation block defaults to pending
      Given a bdd mapping with an empty automation mapping
      When normalize_bdd_metadata is called
      Then automation.status defaults to "pending"

    @bdd-normalize-automation-invalid-status
    Example: Invalid automation status falls back to pending with a warning
      Given a bdd mapping with automation.status set to "done"
      When normalize_bdd_metadata is called
      Then automation.status is "pending"
      And a warning mentions the invalid status

    @bdd-normalize-automation-non-mapping
    Example: Non-mapping automation block is fatal
      Given a bdd mapping with automation as a list
      When normalize_bdd_metadata is called
      Then the returned example is None
      And a warning mentions automation must be a mapping

    @bdd-normalize-automation-feature-file-safety
    Example: Unsafe feature_file path is rejected
      Given a bdd mapping with automation.feature_file containing ".."
      When normalize_bdd_metadata is called
      Then automation.feature_file is empty
      And a warning mentions the path is unsafe

    @bdd-normalize-automation-command-type
    Example: Non-string command is rejected
      Given a bdd mapping with automation.command as an integer
      When normalize_bdd_metadata is called
      Then automation.command is empty
      And a warning mentions command must be a string
