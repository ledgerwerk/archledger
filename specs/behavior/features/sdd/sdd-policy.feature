@area-sdd @feature-sdd-policy
Feature: SDD traceability policy engine

  The SDD policy engine evaluates traceability contracts on loaded records,
  checking acceptance criteria, implementation refs, test refs, and BDD
  metadata.

  @rule-options
  Rule: SDD options are resolved from config and CLI overrides

    @bdd-sdd-options-from-config
    Example: Config provides default SDD options
      Given a project config with sdd.require_acceptance_criteria True
      When sdd_options_from_config is called
      Then require_acceptance_criteria is True

    @bdd-sdd-options-cli-override
    Example: CLI override wins over config default
      Given a project config with sdd.require_acceptance_criteria True
      When sdd_options_from_config is called with require_acceptance_criteria False
      Then require_acceptance_criteria is False

  @rule-check
  Rule: SDD check enforces traceability contracts

    @bdd-sdd-check-passes
    Example: Records meeting all contracts pass SDD check
      Given records with acceptance criteria, source refs, and test refs
      When sdd check is run
      Then no SDD violations are reported

    @bdd-sdd-check-missing-ac
    Example: Accepted record without acceptance criteria is flagged
      Given an accepted record without acceptance criteria
      When sdd check is run with require_acceptance_criteria True
      Then an SDD-AC-MISSING violation is reported

    @bdd-sdd-check-missing-test-refs
    Example: Accepted record without test refs is flagged
      Given an accepted record without test_refs
      When sdd check is run with require_test_refs True
      Then an SDD-TEST-MISSING violation is reported

    @bdd-sdd-check-missing-implementation
    Example: Accepted record without source refs is flagged
      Given an accepted record without source_refs
      When sdd check is run with require_implementation_refs True
      Then an SDD-IMPL-MISSING violation is reported

    @bdd-sdd-check-placeholder-body
    Example: Accepted record with placeholder body is flagged
      Given an accepted record with a template placeholder body
      When sdd check is run
      Then an SDD-PLACEHOLDER violation is reported

  @rule-bdd-gwt
  Rule: Behavior records require BDD Given/When/Then

    @bdd-sdd-check-bdd-gwt
    Example: Behavior record without BDD metadata is flagged
      Given a behavior record without bdd metadata
      When sdd check is run with require_bdd_gwt True
      Then a BDD-GWT-MISSING violation is reported

  @rule-pr-check
  Rule: PR check validates changed files against records

    @bdd-sdd-pr-unlinked-file
    Example: Changed file not linked to any record is flagged
      Given a changed file with no linked record
      When sdd pr check is run
      Then an SDD-PR-UNLINKED violation is reported
