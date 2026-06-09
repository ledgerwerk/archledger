@area-repository @feature-archive-and-doctor
Feature: Archive and doctor repair

  # Archiving must preserve ledger sequence integrity. Doctor repair may create
  # safe tombstones or missing required sections, but it must refuse ambiguous
  # duplicate or manually resegmented states.

  @rule-archive
  Rule: Archive moves records out of the live set while preserving numbers

    @bdd-archive-moves-record
    Example: Archive moves a record and removes it from normal list output
      Given an initialized workspace with a live accepted record
      When archledger archive is run for that record with a reason
      Then the record is moved under the archive
      And archledger list excludes it by default

    @bdd-archive-tombstone-validates
    Example: Archive tombstones are accepted by check and build
      Given a workspace with archive tombstone records
      When archledger check and build are run
      Then no tombstone validation errors are reported

  @rule-sequence-check
  Rule: Check detects ledger sequence gaps and duplicates

    @bdd-doctor-check-missing-number
    Example: Missing ledger number fails check
      Given a workspace whose live and archive records skip a ledger number
      When archledger check is run
      Then an error reports the missing ledger ID

    @bdd-doctor-check-duplicate-id
    Example: Duplicate ledger IDs fail check
      Given two record files with the same ledger ID
      When archledger check is run
      Then an error reports duplicate ledger IDs

    @bdd-doctor-check-filename-id-mismatch
    Example: Filename and front matter ID must match
      Given a record whose filename stem differs from its front matter ID
      When archledger check is run
      Then an error reports the mismatch

  @rule-repair
  Rule: Doctor repair performs only safe deterministic repairs

    @bdd-doctor-repair-missing-number-tombstone
    Example: Repair creates tombstone for a missing ledger number
      Given a workspace with a missing ledger number
      When archledger doctor --repair is run
      Then an archive tombstone is created for the missing number
      And a subsequent check succeeds

    @bdd-doctor-repair-required-section
    Example: Repair recreates missing required section files
      Given an initialized arc42 workspace with a missing required section file
      When archledger doctor --repair is run
      Then the missing section file is recreated

    @bdd-doctor-repair-refuses-duplicates
    Example: Repair refuses duplicate IDs
      Given a workspace with duplicate ledger IDs
      When archledger doctor --repair is run
      Then no files are changed
      And the command reports that duplicate IDs must be fixed manually

    @bdd-doctor-repair-refuses-manual-segment-change
    Example: Repair refuses after manual segment mode change
      Given a workspace initialized with flat IDs
      And the config was manually changed to type segment mode
      When archledger doctor --repair is run
      Then no archive tombstones are generated for inferred segment gaps
      And the command reports that renumbering is required

    @bdd-doctor-repair-stale-tombstone-collision
    Example: Stale generated tombstone collision is not silently overwritten
      Given a generated archive tombstone conflicts with a newly segmented living record
      When archledger doctor --repair is run
      Then the command refuses the repair unless explicit pruning is requested
