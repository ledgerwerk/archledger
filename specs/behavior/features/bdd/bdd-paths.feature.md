`@area-bdd` `@feature-bdd-paths`

# Feature: BDD path conventions detect deprecated locations

Path helpers identify deprecated BDD feature file locations and
produce explanatory messages pointing to the recommended location.

`@rule-deprecated-detection`

## Rule: Deprecated BDD feature paths are identified

`@bdd-paths-deprecated-prefixes`

### Example: Paths under tests/bdd/features are deprecated

- Given a path starting with "tests/bdd/features/"
- When is_deprecated_bdd_feature_path is called
- Then the result is True

`@bdd-paths-deprecated-behavior`

### Example: Paths under tests/behavior/features are deprecated

- Given a path starting with "tests/behavior/features/"
- When is_deprecated_bdd_feature_path is called
- Then the result is True

`@bdd-paths-deprecated-specs-bdd`

### Example: Paths under specs/bdd/features are deprecated

- Given a path starting with "specs/bdd/features/"
- When is_deprecated_bdd_feature_path is called
- Then the result is True

`@rule-recommended-path`

## Rule: Recommended paths are not deprecated

`@bdd-paths-recommended-not-deprecated`

### Example: Paths under specs/behavior/features are not deprecated

- Given a path starting with "specs/behavior/features/"
- When is_deprecated_bdd_feature_path is called
- Then the result is False

`@rule-deprecation-message`

## Rule: Deprecation messages are explanatory

`@bdd-paths-deprecation-message`

### Example: Deprecation message includes recommended path

- Given a deprecated feature file path
- When deprecated_bdd_feature_path_message is called
- Then the message mentions "deprecated"
- And the message includes the recommended path template
