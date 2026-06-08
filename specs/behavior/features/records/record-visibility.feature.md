`@area-records` `@feature-record-visibility`

# Feature: Record visibility filtering

Records are filtered by status for display in assembled documents.

`@rule-visibility`

## Rule: Visibility depends on status and filter flags

`@bdd-records-visible-proposed`

### Example: Proposed records are visible by default

- Given a record with status "proposed"
- When is_visible_status is called with default flags
- Then the result is True

`@bdd-records-visible-accepted`

### Example: Accepted records are visible by default

- Given a record with status "accepted"
- When is_visible_status is called with default flags
- Then the result is True

`@bdd-records-visible-draft-hidden`

### Example: Draft records are hidden unless include_draft is set

- Given a record with status "draft"
- When is_visible_status is called with include_draft False
- Then the result is False

`@bdd-records-visible-draft-shown`

### Example: Draft records are shown when include_draft is set

- Given a record with status "draft"
- When is_visible_status is called with include_draft True
- Then the result is True

`@bdd-records-visible-superseded-hidden`

### Example: Superseded records are hidden by default

- Given a record with status "superseded"
- When is_visible_status is called with include_superseded False
- Then the result is False

`@bdd-records-visible-superseded-shown`

### Example: Superseded records are shown when include_superseded is set

- Given a record with status "superseded"
- When is_visible_status is called with include_superseded True
- Then the result is True
