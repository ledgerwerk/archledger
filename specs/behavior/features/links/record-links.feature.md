`@area-links` `@feature-record-links`

# Feature: Record link normalization

Links describe directed relationships between records. Link normalization
validates shape and relationship type.

`@rule-normalization`

## Rule: Links are normalized from front-matter metadata

`@bdd-links-normalize-valid`

### Example: Valid link is normalized correctly

- Given a link with rel "satisfies" and target "al_0001"
- When normalize_links is called
- Then a RecordLink is returned with rel "satisfies" and target "al_0001"

`@bdd-links-normalize-invalid-rel`

### Example: Invalid relationship type is rejected

- Given a link with rel "invalid_rel"
- When normalize_links is called
- Then a warning about invalid rel is reported

`@bdd-links-normalize-empty-target`

### Example: Empty target is rejected

- Given a link with rel "satisfies" and empty target
- When normalize_links is called
- Then a warning about empty target is reported

`@bdd-links-normalize-none`

### Example: None links returns empty tuple

- Given a None links value
- When normalize_links is called
- Then an empty tuple is returned with no warnings

`@bdd-links-normalize-non-list`

### Example: Non-list links value is rejected

- Given a links value that is a string
- When normalize_links is called
- Then a warning about list type is reported

`@bdd-links-normalize-reason`

### Example: Link reason is preserved

- Given a link with rel "satisfies", target "al_0001", and reason "because"
- When normalize_links is called
- Then the RecordLink reason is "because"
