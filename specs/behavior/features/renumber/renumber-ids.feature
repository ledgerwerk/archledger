@area-renumber @feature-renumber-ids
Feature: ID renumbering

  Renumber changes the ID prefix, width, or segment mode across all
  records in a workspace.

  @rule-dry-run
  Rule: Dry run shows planned changes without mutating

    @bdd-renumber-dry-run
    @req-REQ-0013
    @ac-AC-0130
    Example: Dry run does not rename files
      Given a workspace with records using prefix "al" and width 4
      When renumber is run with --dry-run to prefix "ax" and width 6
      Then no files are renamed
      And the result shows planned renames

  @rule-apply
  Rule: Apply renames files and updates frontmatter

    @bdd-renumber-apply-renames
    @req-REQ-0013
    @ac-AC-0131
    Example: Apply renames record files to new ID format
      Given a workspace with record "al_0001.md"
      When renumber is run with --apply to prefix "ax" and width 6
      Then the file is renamed to "ax_000001.md"

    @bdd-renumber-apply-updates-frontmatter
    @req-REQ-0013
    @ac-AC-0132
    Example: Apply updates the id field in frontmatter
      Given a workspace with record "al_0001.md"
      When renumber is run with --apply to prefix "ax" and width 6
      Then the frontmatter id is "ax_000001"

    @bdd-renumber-apply-updates-references
    @req-REQ-0013
    @ac-AC-0133
    Example: Apply rewrites references to old IDs in other records
      Given a record that references "al_0001" in its body
      When renumber is run with --apply to prefix "ax" and width 6
      Then the reference is rewritten to "ax_000001"

    @bdd-renumber-apply-updates-config
    @req-REQ-0013
    @ac-AC-0134
    Example: Apply updates the config with new ID settings
      Given a workspace with prefix "al" and width 4
      When renumber is run with --apply to prefix "ax" and width 6
      Then the config has prefix "ax" and width 6

  @rule-quarantine
  Rule: Invalid records are quarantined during renumber

    @bdd-renumber-quarantine
    @req-REQ-0013
    @ac-AC-0135
    Example: Records with invalid IDs are quarantined
      Given a workspace with a file that has an invalid ID
      When renumber is run
      Then the invalid file is moved to quarantine
