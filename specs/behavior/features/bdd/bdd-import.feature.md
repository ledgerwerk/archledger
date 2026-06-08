`@area-bdd` `@feature-bdd-import`

# Feature: BDD import creates records from Gherkin feature files

The importer reads a Gherkin feature file, creates one archledger
record per scenario, writes BDD metadata to front matter, and
replaces the template body with Given/When/Then steps.

`@rule-import-creation`

## Rule: Import creates records with correct metadata

`@bdd-import-creates-records`

### Example: Feature file with two scenarios creates two records

- Given an initialized archledger project
- And a feature file with two scenarios
- When bdd import is called with kind runtime-scenario and status accepted
- Then two records are created
- And each record has bdd metadata with feature, scenario, tags, and GWT steps
- And each record has a source_refs entry with role documents

`@bdd-import-writes-body`

### Example: Imported record body contains GWT steps

- Given an initialized archledger project
- And a feature file with a scenario
- When bdd import is called
- Then the record body contains Given/When/Then prefixed steps

`@bdd-import-quality-scenario`

### Example: Quality scenario kind is accepted

- Given an initialized archledger project
- And a feature file with a scenario
- When bdd import is called with kind quality-scenario
- Then the record type is quality_scenario

`@rule-import-warnings`

## Rule: Import warns on edge cases

`@bdd-import-deprecated-path`

### Example: Deprecated feature file path produces a warning

- Given an initialized archledger project
- And a feature file in a deprecated location like tests/bdd/features/
- When bdd import is called
- Then a deprecation warning is included in the response

`@bdd-import-missing-steps`

### Example: Scenarios missing GWT steps produce warnings

- Given a feature file with a scenario that has empty given/when/then
- When bdd import is called
- Then a warning mentions the scenario is missing steps

`@rule-import-validation`

## Rule: Import validates inputs

`@bdd-import-refuses-missing-file`

### Example: Non-existent feature file raises FileNotFoundError

- Given a path that does not exist on disk
- When bdd import is called
- Then a FileNotFoundError is raised

`@bdd-import-normalizes-kind`

### Example: Hyphenated kind is normalized to underscore

- Given an initialized archledger project
- And a feature file with a scenario
- When bdd import is called with kind "runtime-scenario"
- Then the record type is "runtime_scenario"
