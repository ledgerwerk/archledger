`@area-bdd` `@feature-bdd-inspect`

# Feature: BDD inspection lists records and summarizes coverage

The list and status commands produce structured summaries of BDD
metadata across all records, with optional filters.

`@rule-list`

## Rule: BDD list enumerates records with BDD metadata

`@bdd-list-all-records`

### Example: List returns all records with bdd metadata

- Given a project with multiple records some carrying bdd metadata
- When list_bdd_records is called without filters
- Then only records with bdd metadata appear in the result

`@bdd-list-filter-automation`

### Example: Automation status filter narrows results

- Given records with mixed automation statuses
- When list_bdd_records is called with automation_filter=automated
- Then only records with automation.status=automated are returned

`@bdd-list-invalid-metadata`

### Example: Invalid metadata entries are included but marked invalid

- Given a record with structurally invalid bdd metadata
- When list_bdd_records is called
- Then the entry appears with valid=False

`@rule-status`

## Rule: BDD status summarizes coverage dimensions

`@bdd-status-totals`

### Example: Status reports totals for examples and invalid metadata

- Given a project with valid and invalid BDD records
- When bdd_status_summary is called
- Then totals include examples count and invalid_metadata count

`@bdd-status-coverage`

### Example: Coverage includes complete GWT, linked, automated, pending

- Given a project with various BDD records
- When bdd_status_summary is called
- Then coverage includes complete_gwt, linked_feature_files, automated, and pending
- And each dimension has covered and total counts
