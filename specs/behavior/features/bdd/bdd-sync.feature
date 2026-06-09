@area-bdd @feature-bdd-sync
Feature: BDD sync detects drift between records and feature files

  Sync compares BDD metadata on records against linked Gherkin feature
  files, reporting missing files, scenario drift, GWT mismatches,
  and orphan scenarios.

  @rule-sync-drift
  Rule: Sync detects structural drift between records and feature files

    @bdd-sync-no-drift
    Example: Matching records and feature files produce no findings
      Given a project with a BDD record linked to a feature file
      And the record scenario and GWT steps match the feature file exactly
      When bdd sync --check is called
      Then no drift findings are reported

    @bdd-sync-file-missing
    Example: Linked feature file that does not exist is an error
      Given a BDD record linking to a non-existent feature file
      When bdd sync --check is called
      Then a BDD-SYNC-FILE-MISSING finding is reported

    @bdd-sync-scenario-missing
    Example: Record scenario absent from feature file is reported
      Given a BDD record with a scenario name not present in the linked feature file
      When bdd sync --check is called
      Then a BDD-SYNC-SCENARIO-MISSING finding is reported

    @bdd-sync-gwt-mismatch
    Example: Modified GWT steps produce a mismatch finding
      Given a BDD record with given steps that differ from the feature file
      When bdd sync --check is called
      Then a BDD-SYNC-GWT-MISMATCH finding is reported

    @bdd-sync-orphan-scenario
    Example: Extra scenarios in the feature file are reported as orphans
      Given a feature file with a scenario that has no matching BDD record
      When bdd sync --check is called
      Then a BDD-SYNC-ORPHAN-SCENARIO finding is reported

  @rule-sync-metadata
  Rule: Sync reports invalid BDD metadata

    @bdd-sync-invalid-metadata
    Example: Records with structurally invalid BDD metadata are reported
      Given a record with bdd metadata that fails normalization
      When bdd sync --check is called
      Then a BDD-SYNC-INVALID-METADATA finding is reported

  @rule-sync-paths
  Rule: Sync warns about deprecated feature paths

    @bdd-sync-deprecated-path
    Example: Deprecated feature file location produces a warning
      Given a BDD record linking to a file in tests/bdd/features/
      When bdd sync --check is called
      Then a BDD-FEATURE-PATH-CONVENTION finding is reported
