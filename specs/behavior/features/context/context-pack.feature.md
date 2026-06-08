`@area-context` `@feature-context-pack`

# Feature: Context pack building for agents

Context packs provide focused architecture information for coding agents,
selecting only records relevant to a file, record, or set of changes.

`@rule-file-context`

## Rule: File context includes records whose source_refs match the file

`@bdd-context-file-matches-refs`

### Example: Records with matching source_refs are included

- Given a record with source_ref pointing to "src/main.py"
- When build_context_for_file is called with "src/main.py"
- Then the record appears in the context pack

`@bdd-context-file-includes-linked`

### Example: Linked records are included transitively

- Given a record linked to another record
- When build_context_for_file is called for the first record's file
- Then both records appear in the context pack

`@bdd-context-file-caps-records`

### Example: Context pack respects max_records limit

- Given 25 records relevant to a file
- When build_context_for_file is called with max_records 20
- Then at most 20 records appear in the context pack

`@bdd-context-file-schema`

### Example: Context pack uses archledger.context.v1 schema

- Given any workspace
- When build_context_for_file is called
- Then the response schema is "archledger.context.v1"

`@rule-record-context`

## Rule: Record context includes the record and its links

`@bdd-context-record-includes-links`

### Example: Record context includes outgoing and incoming links

- Given a record with outgoing and incoming links
- When build_context_for_record is called
- Then linked records appear in the context pack

`@bdd-context-record-not-found`

### Example: Missing record returns empty context

- Given no record with id "al_9999"
- When build_context_for_record is called with "al_9999"
- Then an empty records list is returned

`@rule-changed-context`

## Rule: Changed context includes records impacted by file changes

`@bdd-context-changed-impacted`

### Example: Changed files surface impacted records

- Given a source change affecting a tracked file
- When build_context_for_changed is called
- Then impacted records appear in the context pack
