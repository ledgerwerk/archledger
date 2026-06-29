@area-ids @feature-ledger-id-segments
Feature: ID segment mode configuration

  The segment mode determines whether IDs include a type segment between
  the prefix and number.

  @rule-segment-mode-none
  Rule: Segment mode "none" produces flat IDs

    @bdd-ids-segment-none-format
    @req-REQ-0007
    @ac-AC-0076
    Example: Format produces flat ID when segment mode is none
      Given a LedgerIdFormat with segment mode "none"
      When format is called with number 5
      Then the result is "al_0005"

    @bdd-ids-segment-none-ignores-segment
    @req-REQ-0007
    @ac-AC-0077
    Example: Format ignores segment parameter when mode is none
      Given a LedgerIdFormat with segment mode "none"
      When format is called with number 5 and segment "req"
      Then the result is "al_0005"

  @rule-segment-mode-type
  Rule: Segment mode "type" includes the type in the ID

    @bdd-ids-segment-type-format
    @req-REQ-0007
    @ac-AC-0078
    Example: Format includes type segment when mode is type
      Given a LedgerIdFormat with segment mode "type"
      When format is called with number 5 and segment "adr"
      Then the result is "al_adr_0005"

    @bdd-ids-segment-type-requires-segment
    @req-REQ-0007
    @ac-AC-0079
    Example: Format raises when segment is missing in type mode
      Given a LedgerIdFormat with segment mode "type"
      When format is called with number 5 and no segment
      Then a ValueError is raised

  @rule-segment-validation
  Rule: Segment values are validated

    @bdd-ids-segment-validate-valid
    @req-REQ-0007
    @ac-AC-0080
    Example: Valid segment passes validation
      Given a segment "req-01"
      When validate_id_segment is called
      Then the normalized segment is "req-01"

    @bdd-ids-segment-validate-invalid
    @req-REQ-0007
    @ac-AC-0081
    Example: Invalid segment fails validation
      Given a segment "REQ"
      When validate_id_segment is called
      Then a ValueError is raised

    @bdd-ids-segment-validate-empty
    @req-REQ-0007
    @ac-AC-0082
    Example: Empty segment fails validation
      Given a segment ""
      When validate_id_segment is called
      Then a ValueError is raised
