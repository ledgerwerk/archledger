@area-repository @feature-repository-mutation
Feature: Repository mutation CLI

  The mutation CLI safely updates individual records while preserving
  Archledger versioning and validation rules.

  @rule-typed-metadata
  Rule: Metadata mutation is type-aware and rollback-safe

    @bdd-mutation-cli-json-list
    @req-REQ-0014
    Example: JSON metadata input stores list data
      Given a workspace with runtime record "runtime-0013"
      When `archledger record meta set runtime-0013 participants --json-value '["caller", "service"]'` is run
      Then the record metadata field `participants` is a YAML list with `caller` and `service`

    @bdd-mutation-cli-rejects-plain-string
    @req-REQ-0014
    Example: Plain string input is rejected for list metadata
      Given a workspace with runtime record "runtime-0013"
      When `archledger record meta set runtime-0013 participants "caller; service"` is run
      Then the command fails with an expected-list error
      And the record file bytes and version remain unchanged

    @bdd-mutation-cli-option-like-string
    @req-REQ-0014
    Example: Explicit string input stores option-like values
      Given a workspace with requirement record "content-0013"
      When `archledger record meta set content-0013 source --string-value "--json envelopes are supported"` is run
      Then the record metadata field `source` is the literal string `--json envelopes are supported`

  @rule-body
  Rule: Body commands modify record content

    @bdd-mutation-cli-body-set
    @req-REQ-0014
    Example: Body set command replaces record body
      Given a workspace with record "content-0013.md"
      When `archledger record body set content-0013 --from-file /tmp/body.md` is run
      Then the record body matches `/tmp/body.md`

  @rule-record-apply
  Rule: Record export and apply round-trip one record safely

    @bdd-mutation-cli-export-apply
    @req-REQ-0014
    Example: Export and apply updates one record once
      Given a workspace with requirement record "content-0013"
      When `archledger record export content-0013 --output /tmp/content-0013.md` is run
      And the exported file body is edited
      And `archledger record apply content-0013 --from-file /tmp/content-0013.md` is run
      Then the record body is updated
      And the record version increments exactly once

    @bdd-mutation-cli-apply-rollback
    @req-REQ-0014
    Example: Apply rejects identity changes
      Given a workspace with requirement record "content-0013"
      When an exported record file changes `kind`
      And `archledger record apply content-0013 --from-file /tmp/content-0013.md` is run
      Then the command fails
      And the original record remains unchanged
