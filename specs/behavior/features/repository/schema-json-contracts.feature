@area-repository @feature-schema-json-contracts
Feature: JSON schema and CLI payload contracts

  # Machine-readable CLI commands must expose stable schema names and payload
  # shapes. Schema installation must be safe against accidental overwrites.

  @rule-schema-command
  Rule: Schema command lists supported schema contracts

    @bdd-schema-json-lists-contracts
    Example: Schema JSON lists record types, statuses, sections, and formats
      Given an initialized workspace
      When archledger schema is run with JSON output
      Then record types, statuses, sections, and output formats are listed

    @bdd-schema-jsonschema-target-returned
    Example: JSON schema install reports target path
      Given an empty schema output directory
      When archledger schema install is run with JSON output
      Then the response includes the schema target path

    @bdd-schema-install-refuses-overwrite
    Example: Schema install refuses overwrite without force
      Given a schema file already exists at the target path
      When archledger schema install is run without force
      Then the command fails and does not overwrite the file

  @rule-cli-json-shapes
  Rule: Core CLI JSON responses retain stable shapes

    @bdd-json-status-shape
    Example: Status JSON shape is stable
      Given an initialized workspace
      When archledger status is run with JSON output
      Then the result uses the expected status schema fields

    @bdd-json-check-shape
    Example: Check JSON shape is stable
      Given an initialized workspace
      When archledger check is run with JSON output
      Then errors, warnings, and records_checked fields are present

    @bdd-json-paths-shape
    Example: Paths JSON shape includes archive and source state paths
      Given an initialized workspace
      When archledger paths is run with JSON output
      Then archive and source state paths are present

    @bdd-json-missing-record-error
    Example: Missing record returns structured JSON error
      Given no record exists with the requested ID
      When archledger show is run with JSON output
      Then the response contains a structured error object

  @rule-payload-schemas
  Rule: Feature-specific JSON payloads match bundled schemas

    @bdd-schema-sdd-check-v2
    Example: SDD check payload matches bundled schema
      Given a workspace with SDD enabled
      When archledger sdd check is run with JSON output
      Then the payload validates against archledger.sdd-check.v2 schema

    @bdd-schema-bdd-export
    Example: BDD export payload matches bundled schema
      Given a record with valid bdd metadata
      When archledger bdd export is run with JSON output
      Then the payload validates against archledger.bdd-export.v1 schema

    @bdd-schema-bdd-sync
    Example: BDD sync payload matches bundled schema
      Given a record linked to a feature file
      When archledger bdd sync is run with JSON output
      Then the payload validates against archledger.bdd-sync.v1 schema

    @bdd-schema-sdd-init
    Example: SDD init payload matches bundled schema
      Given an initialized workspace
      When archledger sdd init is run with JSON output
      Then the payload validates against archledger.sdd-init.v1 schema

    @bdd-schema-sdd-explain
    Example: SDD explain payload matches bundled schema
      Given a known SDD rule code
      When archledger sdd explain is run with JSON output
      Then the payload validates against archledger.sdd-explain.v1 schema
