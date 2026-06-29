@area-repository @feature-repository-check
Feature: Repository check and validation

  The check command validates all records for structural issues, content
  warnings, and archive tombstone handling.

  @rule-check
  Rule: Check reports errors and warnings for invalid records

    @bdd-repo-check-passes
    @req-REQ-0014
    @ac-AC-0184
    Example: Valid workspace passes check
      Given an initialized workspace with valid records
      When archledger check is run
      Then no errors are reported

    @bdd-repo-check-archive-tombstones
    @req-REQ-0014
    @ac-AC-0185
    Example: Archive tombstones are accepted without errors
      Given a workspace with an archive_tombstone record
      When archledger check is run
      Then no errors are reported for the tombstone

    @bdd-repo-check-canonical-config
    @req-REQ-0014
    @ac-AC-0186
    Example: Canonical config wins when both exist
      Given a workspace with both .archledger.toml and archledger.toml
      When archledger check is run
      Then a warning about duplicate config is emitted

  @rule-snapshot
  Rule: Snapshot captures source state for change tracking

    @bdd-repo-snapshot-creates-state
    @req-REQ-0014
    @ac-AC-0187
    Example: Snapshot writes source-state JSON
      Given an initialized workspace
      When archledger snapshot is run
      Then source-state.json is created with file hashes

    @bdd-repo-snapshot-respects-disabled
    @req-REQ-0014
    @ac-AC-0188
    Example: Snapshot is skipped when tracking is disabled
      Given a workspace with tracking disabled
      When archledger snapshot is run
      Then no source-state.json is created
