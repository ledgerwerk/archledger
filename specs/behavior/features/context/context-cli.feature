@area-context @feature-context-cli
Feature: Context CLI commands

  The context CLI provides commands for building context packs for
  coding agents.

  @rule-changed
  Rule: Context changed uses source baseline for change detection

    @bdd-context-changed-baseline
    @req-REQ-0004
    @ac-AC-0033
    Example: Context changed uses source baseline without crashing
      Given a workspace with a source baseline
      When archledger context changed is run
      Then the command completes without error

    @bdd-context-changed-no-baseline
    @req-REQ-0004
    @ac-AC-0034
    Example: Context changed handles missing baseline gracefully
      Given a workspace without a source baseline
      When archledger context changed is run
      Then the command completes with empty changeset

  @rule-file
  Rule: Context file builds pack for a specific file

    @bdd-context-file-json
    @req-REQ-0004
    @ac-AC-0035
    Example: Context file returns JSON payload
      Given a workspace with records
      When archledger context file src/main.py --json is run
      Then a JSON payload with schema "archledger.context.v1" is returned

  @rule-record
  Rule: Context record builds pack for a specific record

    @bdd-context-record-json
    @req-REQ-0004
    @ac-AC-0036
    Example: Context record returns JSON payload
      Given a workspace with record "al_0001"
      When archledger context record al_0001 --json is run
      Then a JSON payload with the record is returned
