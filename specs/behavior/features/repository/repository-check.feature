@area-repository @feature-repository-check
Feature: Repository check and validation

  The check command validates record structure, metadata shape, and archive
  integrity without mutating source files.

  @rule-check
  Rule: Check reports errors and warnings for invalid records

    @bdd-repo-check-passes
    @req-REQ-0014
    Example: Valid workspace passes check
      Given an initialized workspace with valid records
      When `archledger check` is run
      Then no errors are reported

    @bdd-repo-check-typed-metadata-error
    @req-REQ-0014
    Example: Type-specific metadata errors are reported
      Given a workspace with runtime record "runtime-0013"
      And the `participants` metadata field was manually corrupted to a plain string
      When `archledger check` is run
      Then the result includes an error saying the field must be a list of strings

  @rule-archive
  Rule: Archived records keep structural validation but skip live completeness warnings

    @bdd-repo-check-archived-no-runtime-warning
    @req-REQ-0014
    Example: Archived runtime record skips live completeness warnings
      Given an archived runtime record with no participants
      When `archledger check --strict` is run
      Then no runtime completeness warning is emitted for that archived record

    @bdd-repo-check-archived-outside-active-storage
    @req-REQ-0014
    Example: Archived status outside archive storage still fails
      Given a runtime record in active storage with `status: archived`
      When `archledger check` is run
      Then the result includes an error saying the archived record is outside archive storage

    @bdd-repo-check-non-archived-inside-archive-storage
    @req-REQ-0014
    Example: Non-archived status inside archive storage still fails
      Given a record file inside archive storage with `status: proposed`
      When `archledger check` is run
      Then the result includes an error saying archive files must use archived status

  @rule-snapshot
  Rule: Snapshot captures source state for change tracking

    @bdd-repo-snapshot-creates-state
    @req-REQ-0014
    Example: Snapshot writes source-state JSON
      Given an initialized workspace
      When `archledger snapshot` is run
      Then source-state.json is created with file hashes
