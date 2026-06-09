@area-records @feature-record-validation
Feature: Record validation

  Records are validated for structural correctness: required fields,
  valid types, statuses, sections, ID-filename consistency, and format.

  @rule-required-fields
  Rule: Records must have all required fields populated

    @bdd-records-validate-empty-title
    Example: Empty title is rejected
      Given a record with an empty title
      When validate_record is called
      Then an issue "Title must not be empty" is reported

    @bdd-records-validate-bad-type
    Example: Unknown record type is rejected
      Given a record with type "nonexistent"
      When validate_record is called
      Then an issue "Unknown record type" is reported

    @bdd-records-validate-bad-status
    Example: Unknown status is rejected
      Given a record with status "invalid"
      When validate_record is called
      Then an issue "Unknown status" is reported

    @bdd-records-validate-bad-section
    Example: Unknown section is rejected
      Given a record with section "nonexistent"
      When validate_record is called
      Then an issue "Unknown section" is reported

  @rule-id-filename-consistency
  Rule: Record ID must match the filename stem

    @bdd-records-validate-id-mismatch
    Example: ID-filename mismatch is reported
      Given a record with id "al_0001" and filename stem "al_0002"
      When validate_record is called
      Then an issue "does not match filename stem" is reported

    @bdd-records-validate-id-format
    Example: ID must match configured format pattern
      Given a record with id "bad_id"
      When validate_record is called
      Then an issue "must match" is reported

  @rule-order
  Rule: Order must be an integer

    @bdd-records-validate-order-bool
    Example: Boolean order is rejected
      Given a record with order True
      When validate_record is called
      Then an issue "Order must be an integer" is reported

    @bdd-records-validate-order-string
    Example: String order is rejected
      Given a record with order "five"
      When validate_record is called
      Then an issue "Order must be an integer" is reported
