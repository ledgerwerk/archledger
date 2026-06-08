`@area-mutations` `@feature-record-mutations`

# Feature: Record mutation commands

Patch-safe mutation commands modify individual record fields or body
without touching other metadata.

`@rule-status`

## Rule: Status can be changed on a record

`@bdd-mutation-set-status`

### Example: Set status updates the record

- Given a record with status "draft"
- When set_record_status is called with "proposed"
- Then the record status is "proposed"
- And updated_at is refreshed

`@rule-meta`

## Rule: Arbitrary metadata keys can be set

`@bdd-mutation-set-meta`

### Example: Set meta updates a single key

- Given a record with no "priority" key
- When set_record_meta is called with key "priority" and value "high"
- Then the record has priority "high"

`@rule-body`

## Rule: Record body can be replaced or appended

`@bdd-mutation-replace-body`

### Example: Replace body replaces entire content

- Given a record with body "old content"
- When replace_record_body is called with "new content"
- Then the record body is "new content"

`@bdd-mutation-append-body`

### Example: Append body adds to existing content

- Given a record with body "existing"
- When append_record_body is called with " added text"
- Then the record body contains "existing" and "added text"

`@rule-source-refs`

## Rule: Source references can be added to a record

`@bdd-mutation-add-source-ref`

### Example: Add source ref appends a new reference

- Given a record with no source_refs
- When add_source_ref is called with path "src/main.py"
- Then the record has a source_ref for "src/main.py"

`@rule-record-id-assertion`

## Rule: Mutations verify the record ID matches

`@bdd-mutation-wrong-id`

### Example: Mutation rejects mismatched record ID

- Given a record with id "al_0001"
- When a mutation is called with record_id "al_0002"
- Then a ValidationError is raised
