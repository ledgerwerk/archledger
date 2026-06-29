@area-ids @feature-ledger-id-format
Feature: Ledger ID format and parsing

  Ledger IDs follow a configurable prefix_width pattern with optional
  type segments. The format engine validates, parses, and round-trips IDs.

  @rule-format
  Rule: Ledger IDs are zero-padded integers with a configurable prefix

    @bdd-ids-format-zero-pad
    @req-REQ-0007
    @ac-AC-0063
    Example: Format pads numbers with leading zeros
      Given a LedgerIdFormat with prefix "al" and width 4
      When format is called with number 7
      Then the result is "al_0007"

    @bdd-ids-format-custom-prefix
    @req-REQ-0007
    @ac-AC-0064
    Example: Format accepts custom prefix and width
      Given a LedgerIdFormat with prefix "ax" and width 6
      When format is called with number 42
      Then the result is "ax_000042"

    @bdd-ids-format-rejects-invalid-number
    @req-REQ-0007
    @ac-AC-0065
    Example: Format rejects non-positive integers
      Given a LedgerIdFormat with default settings
      When format is called with number 0
      Then a ValueError is raised

  @rule-parsing
  Rule: Ledger IDs can be parsed back to their numeric value

    @bdd-ids-parse-roundtrip
    @req-REQ-0007
    @ac-AC-0066
    Example: Parse reverses format for any valid ID
      Given a LedgerIdFormat with prefix "al" and width 4
      When a formatted ID is parsed
      Then the original number is recovered

    @bdd-ids-parse-custom-config
    @req-REQ-0007
    @ac-AC-0067
    Example: Parse respects configured prefix and width
      Given a LedgerIdFormat with prefix "ax" and width 6
      When "ax_000042" is parsed
      Then the number is 42

    @bdd-ids-parse-rejects-wrong-format
    @req-REQ-0007
    @ac-AC-0068
    Example: Parse rejects IDs that do not match configured format
      Given a LedgerIdFormat with prefix "al" and width 4
      When "zz_0001" is parsed
      Then a ValueError is raised

    @bdd-ids-parse-rejects-invalid
    @req-REQ-0007
    @ac-AC-0069
    Example: Parse rejects malformed ID strings
      Given a LedgerIdFormat with default settings
      When "not_an_id" is parsed
      Then a ValueError is raised

  @rule-segmented
  Rule: Segmented IDs include a type segment between prefix and number

    @bdd-ids-segment-format
    @req-REQ-0007
    @ac-AC-0070
    Example: Format produces segmented IDs when segment mode is type
      Given a LedgerIdFormat with segment mode "type"
      When format is called with number 5 and segment "req"
      Then the result is "al_req_0005"

    @bdd-ids-segment-parse
    @req-REQ-0007
    @ac-AC-0071
    Example: Parse extracts segment from segmented IDs
      Given a LedgerIdFormat with segment mode "type"
      When "al_req_0005" is parsed
      Then the number is 5 and the segment is "req"

    @bdd-ids-segment-requires-segment
    @req-REQ-0007
    @ac-AC-0072
    Example: Format requires a segment when segment mode is type
      Given a LedgerIdFormat with segment mode "type"
      When format is called with number 5 and no segment
      Then a ValueError is raised

  @rule-validation
  Rule: ID components are validated on construction

    @bdd-ids-validate-prefix
    @req-REQ-0007
    @ac-AC-0073
    Example: Prefix must match lowercase alphanumeric pattern
      Given a prefix "A"
      When validate_id_prefix is called
      Then a ValueError is raised

    @bdd-ids-validate-width
    @req-REQ-0007
    @ac-AC-0074
    Example: Width must be between 2 and 12
      Given a width of 1
      When validate_id_width is called
      Then a ValueError is raised

    @bdd-ids-validate-segment-mode
    @req-REQ-0007
    @ac-AC-0075
    Example: Segment mode must be none or type
      Given a segment mode "invalid"
      When validate_id_segment_mode is called
      Then a ValueError is raised
