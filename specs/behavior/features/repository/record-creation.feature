@area-repository @feature-record-creation
Feature: Record creation command behavior

  # The new command must allocate monotonically increasing ledger IDs, apply
  # type-specific templates and context options, and report created records in
  # stable human and JSON forms.

  @rule-type-specific-records
  Rule: New command creates records in the correct type directories

    @bdd-new-requirement-record
    Example: Requirement record is created with requirement template
      Given an initialized workspace
      When archledger new requirement is run
      Then a requirement record file is created
      And the body contains the requirement template section

    @bdd-new-black-box-record
    Example: Black box record is created in building blocks
      Given an initialized workspace
      When archledger new black-box is run
      Then a building block record file is created

    @bdd-new-white-box-record
    Example: White box record is created in building blocks
      Given an initialized workspace
      When archledger new white-box is run
      Then a building block record file is created

    @bdd-new-adr-legacy-alias
    Example: ADR alias creates an architecture decision record
      Given an initialized workspace
      When archledger new adr is run
      Then an architecture decision record file is created

    @bdd-new-strategy-item-record
    Example: Strategy item record is created
      Given an initialized workspace
      When archledger new strategy-item is run
      Then a strategy record file is created

  @rule-context-options
  Rule: Type-specific options populate front matter

    @bdd-new-context-interface-partner
    Example: Context interface accepts context kind and partner
      Given an initialized workspace
      When archledger new context-interface is run with context kind and partner
      Then the created record metadata contains those values

    @bdd-new-infrastructure-environment
    Example: Infrastructure accepts environment
      Given an initialized workspace
      When archledger new infrastructure is run with environment production
      Then the created record metadata has environment production

    @bdd-new-quality-scenario-quality-environment
    Example: Quality scenario accepts quality and environment
      Given an initialized workspace
      When archledger new quality-scenario is run with quality and environment
      Then the created record metadata contains quality and environment

    @bdd-new-diagram-options
    Example: Diagram creation accepts diagram options
      Given an initialized workspace
      When archledger new diagram is run with diagram type and renderer
      Then the created record metadata contains diagram type and renderer

  @rule-id-allocation
  Rule: Creation uses configured ID format and never reuses archived numbers

    @bdd-new-configured-id-format
    Example: Configured ID prefix and width are applied
      Given a workspace initialized with id prefix ta and width 3
      When archledger new requirement is run
      Then the created ledger ID starts with ta and has width 3

    @bdd-new-segment-mode-type
    Example: Type segment mode adds record type segment
      Given a workspace initialized with id segment mode type
      When archledger new risk is run
      Then the created ledger ID includes the risk segment

    @bdd-new-custom-record-extension
    Example: Custom record extension increments correctly
      Given a workspace configured to use a custom record extension
      When two requirement records are created
      Then both records have unique increasing ledger numbers

    @bdd-new-does-not-reuse-archived-number
    Example: Archived numbers are not reused
      Given a workspace with an archived record at number 13
      When a new record is created
      Then the new record uses the next number after the archive

    @bdd-new-refuses-when-counter-proves-missing-number
    Example: New refuses allocation when storage counter proves a gap
      Given storage metadata indicates a missing reserved ledger number
      When archledger new requirement is run
      Then the command fails and asks for doctor repair

  @rule-json-and-seed
  Rule: Creation and seeding expose stable automation output

    @bdd-new-json-output
    Example: New command returns JSON payload
      Given an initialized workspace
      When archledger --json new requirement is run
      Then the result contains schema, id, path, and type fields

    @bdd-new-diagram-json-output
    Example: New diagram JSON includes diagram metadata
      Given an initialized workspace
      When archledger --json new diagram is run
      Then the result contains diagram type and output path

    @bdd-seed-arc42-minimal
    Example: Arc42 minimal seed creates starter records
      Given an initialized workspace
      When archledger seed arc42-minimal is run
      Then starter architecture records are created

    @bdd-new-every-record-type
    Example: Every registered record type can be created
      Given an initialized workspace
      When archledger new is run for every registered record type
      Then every creation command succeeds
