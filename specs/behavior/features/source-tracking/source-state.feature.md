`@area-source-tracking` `@feature-source-state`

# Feature: Source state tracking and change detection

Source tracking captures file hashes for change detection between
snapshots.

`@rule-state`

## Rule: Source state records file and directory hashes

`@bdd-source-state-roundtrip`

### Example: Source state serializes and deserializes correctly

- Given a source state with tracked files
- When the state is serialized to JSON and read back
- Then all file paths and hashes are preserved

`@bdd-source-state-relative-paths`

### Example: Source state uses relative paths

- Given a workspace with files
- When a source state snapshot is created
- Then all paths are relative to workspace root

`@bdd-source-state-schema`

### Example: Source state JSON uses correct schema

- Given any workspace
- When a source state snapshot is created
- Then the JSON schema field is "archledger.source-state.v2"

`@rule-changeset`

## Rule: Changeset detects added, modified, and deleted files

`@bdd-changeset-detects-added`

### Example: New files are detected as added

- Given a baseline without "new_file.py"
- When a changeset is computed
- Then "new_file.py" appears as added

`@bdd-changeset-detects-modified`

### Example: Changed files are detected as modified

- Given a baseline with "old_hash" for "file.py"
- And the current file has a different hash
- When a changeset is computed
- Then "file.py" appears as modified

`@bdd-changeset-detects-deleted`

### Example: Removed files are detected as deleted

- Given a baseline with "deleted.py"
- And the file no longer exists
- When a changeset is computed
- Then "deleted.py" appears as deleted

`@bdd-changeset-impacted-records`

### Example: Changeset identifies impacted records

- Given a changed file referenced by a record's source_refs
- When a changeset is computed
- Then the record appears in impacted_records
