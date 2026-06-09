@area-sdd @feature-sdd-lifecycle-commands
Feature: SDD lifecycle commands

  # SDD commands initialize policy, report status, explain rules, manage waivers,
  # compute coverage, and allow scoped checks without weakening the traceability
  # contract.

  @rule-init-status
  Rule: SDD init and status expose enabled contract state

    @bdd-sdd-init-enables-profile
    Example: SDD init enables the profile and writes policy
      Given an arc42 workspace without SDD enabled
      When archledger sdd init is run
      Then the sdd profile is enabled
      And a profiles.sdd policy block is written

    @bdd-sdd-init-strict-seed
    Example: Strict SDD init can seed minimal contract records
      Given an initialized workspace
      When archledger sdd init is run with strict defaults and minimal seed
      Then strict policy defaults are enabled
      And seed records for the SDD contract are created

    @bdd-sdd-init-dry-run
    Example: SDD init dry run reports changes without writing
      Given an initialized workspace
      When archledger sdd init is run with dry run
      Then no config or records are changed
      And the planned changes are reported

    @bdd-sdd-status-json-policy
    Example: SDD status reports policy and enabled profiles
      Given an arc42 workspace with SDD enabled
      When archledger sdd status is run with JSON output
      Then the response includes policy and enabled_profiles

  @rule-policy-management
  Rule: Policy commands show and change effective settings

    @bdd-sdd-policy-show
    Example: Policy show reports effective policy
      Given a workspace with SDD enabled
      When archledger sdd policy show is run
      Then the effective policy settings are reported

    @bdd-sdd-policy-set-updates-config
    Example: Policy set updates the SDD policy block
      Given a workspace with SDD enabled
      When archledger sdd policy set is run with require test refs
      Then the config policy requires test refs

    @bdd-sdd-policy-set-requires-flag
    Example: Policy set requires at least one flag
      Given a workspace with SDD enabled
      When archledger sdd policy set is run without policy flags
      Then the command fails with a usage error

  @rule-explain-waive
  Rule: Rule explanation and waivers are explicit and reversible

    @bdd-sdd-explain-single-rule
    Example: Explain single SDD rule
      Given a known SDD rule code
      When archledger sdd explain is run for that code
      Then the response describes the rule

    @bdd-sdd-explain-all-rules
    Example: Explain all SDD rules
      Given SDD rules are registered
      When archledger sdd explain all is run
      Then every rule code is listed

    @bdd-sdd-explain-unknown-rule
    Example: Unknown SDD rule code fails clearly
      Given an unknown SDD rule code
      When archledger sdd explain is run
      Then the command reports the code is unknown

    @bdd-sdd-waive-add-requires-reason
    Example: Adding waiver requires a reason
      Given a record with an SDD finding
      When archledger sdd waive add is run without a reason
      Then the command fails with a reason-required error

    @bdd-sdd-waive-add-suppresses-rule
    Example: Waiver suppresses matching rule
      Given a record with an SDD finding
      When a waiver is added for that rule and record
      Then subsequent SDD check does not report that finding

    @bdd-sdd-waive-remove-restores-rule
    Example: Removing waiver restores finding
      Given a record with a waiver suppressing an SDD finding
      When the waiver is removed
      Then subsequent SDD check reports the finding again

    @bdd-sdd-waive-unknown-rule-rejected
    Example: Waiver rejects unknown rule code
      Given an unknown SDD rule code
      When archledger sdd waive add is run for that code
      Then the command fails and no waiver is written

  @rule-coverage-scope
  Rule: Coverage and scoped checks expose gaps without scanning unrelated records

    @bdd-sdd-coverage-gaps
    Example: Coverage reports dimensions and gaps
      Given accepted records with missing source refs and test refs
      When archledger sdd coverage is run
      Then the response lists coverage dimensions and gap counts

    @bdd-sdd-coverage-include-bdd
    Example: Coverage can include BDD dimensions
      Given behavior records with BDD metadata
      When archledger sdd coverage is run with include bdd
      Then BDD coverage counts are included

    @bdd-sdd-coverage-by-record
    Example: Coverage by record lists per-record detail
      Given multiple accepted records
      When archledger sdd coverage is run by record
      Then each checked record has a coverage detail entry

    @bdd-sdd-check-scoped-record
    Example: SDD check can target one record
      Given multiple accepted records
      When archledger sdd check is run for one record id
      Then only that record is checked

    @bdd-sdd-check-scoped-kind
    Example: SDD check can target one kind
      Given accepted records of multiple kinds
      When archledger sdd check is run for kind requirement
      Then only requirement records are checked
