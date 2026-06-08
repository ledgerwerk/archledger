`@area-bdd` `@feature-bdd-validate`

# Feature: BDD validation checks metadata and feature file structure

Validation inspects BDD metadata on records and parses Gherkin
feature files without importing, reporting structured findings.

`@rule-record-validation`

## Rule: Record BDD metadata is validated for completeness

`@bdd-validate-valid-record`

### Example: Valid BDD metadata passes validation

- Given a record with structurally complete bdd metadata
- When validate_bdd_record is called
- Then the response is valid with no error-severity findings

`@bdd-validate-absent-metadata`

### Example: Absent BDD metadata is an error

- Given a record without bdd metadata
- When validate_bdd_record is called
- Then a BDD-METADATA-ABSENT finding is reported

`@bdd-validate-gwt-incomplete`

### Example: Missing given/when/then steps are reported

- Given a record with bdd metadata but empty given sequence
- When validate_bdd_record is called
- Then a BDD-GWT-INCOMPLETE finding is reported

`@bdd-validate-automation-status`

### Example: Invalid automation status is an error

- Given a record with bdd.automation.status set to "unknown"
- When validate_bdd_record is called
- Then a BDD-AUTOMATION-STATUS finding is reported

`@bdd-validate-automated-no-command`

### Example: Automated status without command or test_refs is a warning

- Given a record with automation.status=automated but no command
- When validate_bdd_record is called
- Then a BDD-AUTOMATION-COMMAND warning is reported

`@bdd-validate-linked-no-feature`

### Example: Linked status without feature_file is a warning

- Given a record with automation.status=linked but empty feature_file
- When validate_bdd_record is called
- Then a BDD-AUTOMATION-LINK warning is reported

`@bdd-validate-tag-format`

### Example: Empty or whitespace tags produce warnings

- Given a record with bdd tags containing empty or whitespace strings
- When validate_bdd_record is called
- Then a BDD-TAG-FORMAT warning is reported

`@rule-feature-file-validation`

## Rule: Feature files are parse-validated

`@bdd-validate-feature-file`

### Example: Valid feature file passes validation

- Given a workspace with a well-formed feature file
- When validate_bdd_feature_file is called
- Then the response is valid and scenarios are returned

`@bdd-validate-feature-file-missing`

### Example: Non-existent feature file is an error

- Given a path to a file that does not exist
- When validate_bdd_feature_file is called
- Then a BDD-FEATURE-MISSING finding is reported

`@bdd-validate-feature-unsupported`

### Example: Unsupported Gherkin constructs are reported

- Given a feature file containing a Background block
- When validate_bdd_feature_file is called
- Then a BDD-GHERKIN-UNSUPPORTED finding is reported with a line number

`@bdd-validate-no-scenarios`

### Example: Feature file with no scenarios is a warning

- Given a feature file with a Feature header but no scenarios
- When validate_bdd_feature_file is called
- Then a BDD-FEATURE-NO-SCENARIOS warning is reported

`@rule-validate-all`

## Rule: All-records validation iterates the full ledger

`@bdd-validate-all-skip-no-bdd`

### Example: Records without bdd metadata are skipped

- Given a project with mixed records some with and some without bdd
- When validate_bdd_all is called
- Then only records with bdd metadata are checked
