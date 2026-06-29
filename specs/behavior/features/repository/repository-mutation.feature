@area-repository @feature-repository-mutation
Feature: Repository mutation CLI

  The mutation CLI provides commands for updating individual record
  fields and body content.

  @rule-nested-commands
  Rule: Nested mutation commands target specific fields

    @bdd-mutation-cli-status
    @req-REQ-0014
    @ac-AC-0200
    Example: Status command updates record status
      Given a workspace with record "al_0001.md" with status "draft"
      When archledger record al_0001 status set proposed is run
      Then the record status is "proposed"

    @bdd-mutation-cli-meta
    @req-REQ-0014
    @ac-AC-0201
    Example: Meta command sets arbitrary metadata
      Given a workspace with record "al_0001.md"
      When archledger record al_0001 meta set priority high is run
      Then the record has metadata priority "high"

  @rule-body
  Rule: Body commands modify record content

    @bdd-mutation-cli-body-set
    @req-REQ-0014
    @ac-AC-0202
    Example: Body set command replaces record body
      Given a workspace with record "al_0001.md"
      When archledger record al_0001 body set "New content" is run
      Then the record body is "New content"

    @bdd-mutation-cli-body-append
    @req-REQ-0014
    @ac-AC-0203
    Example: Body append command adds to record body
      Given a workspace with record "al_0001.md" with body "Existing"
      When archledger record al_0001 body append " Added" is run
      Then the record body contains "Existing" and "Added"
