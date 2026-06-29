@area-ids @feature-ledger-id-detection
Feature: Ledger ID detection and filename mapping

  IDs can be detected in arbitrary text and mapped to filenames.

  @rule-detection
  Rule: is_ledger_id identifies valid IDs in any context

    @bdd-ids-detect-valid
    @req-REQ-0007
    @ac-AC-0058
    Example: Valid ID string is recognized
      Given the default ID format
      When is_ledger_id is called with "al_0001"
      Then the result is True

    @bdd-ids-detect-invalid
    @req-REQ-0007
    @ac-AC-0059
    Example: Non-ID string is rejected
      Given the default ID format
      When is_ledger_id is called with "hello"
      Then the result is False

    @bdd-ids-detect-non-string
    @req-REQ-0007
    @ac-AC-0060
    Example: Non-string values are rejected
      Given the default ID format
      When is_ledger_id is called with 42
      Then the result is False

  @rule-filename
  Rule: IDs map directly to filenames with the configured extension

    @bdd-ids-filename
    @req-REQ-0007
    @ac-AC-0061
    Example: Filename includes ID and extension
      Given a valid ledger ID "al_0001"
      When filename_for_ledger_id is called with extension ".md"
      Then the result is "al_0001.md"

    @bdd-ids-from-filename
    @req-REQ-0007
    @ac-AC-0062
    Example: ID is extracted from filename stem
      Given a path "al_0001.md"
      When ledger_id_from_filename is called
      Then the result is "al_0001"
