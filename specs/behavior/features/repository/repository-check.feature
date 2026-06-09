@area-repository @feature-repository-check
Feature: Repository check and validation

  The check command validates all records for structural issues, content
  warnings, and archive tombstone handling.

  @rule-check
  Rule: Check reports errors and warnings for invalid records

    @bdd-repo-check-passes
    Example: Valid workspace passes check
      Given an initialized workspace with valid records
      When archledger check is run
      Then no errors are reported

    @bdd-repo-check-archive-tombstones
    Example: Archive tombstones are accepted without errors
      Given a workspace with an archive_tombstone record
      When archledger check is run
      Then no errors are reported for the tombstone

    @bdd-repo-check-canonical-config
    Example: Canonical config wins when both exist
      Given a workspace with both .archledger.toml and archledger.toml
      When archledger check is run
      Then a warning about duplicate config is emitted

  @rule-snapshot
  Rule: Snapshot captures source state for change tracking

    @bdd-repo-snapshot-creates-state
    Example: Snapshot writes source-state JSON
      Given an initialized workspace
      When archledger snapshot is run
      Then source-state.json is created with file hashes

    @bdd-repo-snapshot-respects-disabled
    Example: Snapshot is skipped when tracking is disabled
      Given a workspace with tracking disabled
      When archledger snapshot is run
      Then no source-state.json is created
