@area-bdd @feature-bdd-linking
Feature: BDD metadata set and link commands

  # BDD set and link commands provide a direct way to attach behavior metadata,
  # feature-file references, automation state, and pytest test refs to existing
  # records without importing a whole feature file.

  @rule-set
  Rule: BDD set creates or patches record metadata

    @bdd-set-creates-block
    Example: BDD set creates BDD block
      Given an initialized workspace with a record that has no bdd metadata
      When archledger bdd set is run with feature, scenario, Given, When, and Then
      Then the record front matter contains a valid bdd block

    @bdd-set-patches-existing-block
    Example: BDD set patches existing BDD block
      Given a record with existing bdd metadata
      When archledger bdd set is run with a changed scenario
      Then the existing bdd block is updated without dropping other fields

  @rule-link
  Rule: BDD link connects feature files, scenarios, automation, and tests

    @bdd-link-feature-source-ref
    Example: BDD link sets automation feature file and source ref
      Given a record with valid bdd metadata
      And a feature file under specs/behavior/features
      When archledger bdd link is run with the feature file and scenario tag
      Then automation feature_file and scenario are set
      And source_refs includes the feature file with role documents

    @bdd-link-pytest-test-ref
    Example: BDD link can add pytest test reference
      Given a record with valid bdd metadata
      When archledger bdd link is run with a pytest test nodeid
      Then test_refs includes the pytest test reference

    @bdd-link-automated-requires-command-or-test
    Example: Automated status requires command or test reference
      Given a record with valid bdd metadata
      When archledger bdd link is run with status automated and no command or test ref
      Then the command fails before writing metadata

    @bdd-link-refuses-record-without-bdd
    Example: BDD link refuses records without BDD metadata
      Given a record without bdd metadata
      When archledger bdd link is run
      Then the command fails and no source_refs are added

    @bdd-link-linked-default-status
    Example: BDD import or link defaults automation to linked
      Given a record linked to a feature file without an explicit automation status
      When BDD metadata is written
      Then automation status is linked
