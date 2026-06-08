`@area-sdd` `@feature-sdd-bdd-integration`

# Feature: SDD-BDD integration

The SDD check validates BDD metadata shape and automation status
as part of the traceability contract.

`@rule-bdd-shape`

## Rule: SDD validates BDD metadata structure

`@bdd-sdd-bdd-shape-valid`

### Example: Valid BDD metadata passes SDD shape check

- Given a record with structurally valid bdd metadata
- When sdd bdd check is run
- Then no SDD-BDD violations are reported

`@bdd-sdd-bdd-shape-invalid`

### Example: Structurally invalid BDD metadata fails SDD check

- Given a record with structurally invalid bdd metadata
- When sdd bdd check is run
- Then an SDD-BDD-SHAPE violation is reported

`@rule-deprecated-paths`

## Rule: Deprecated BDD feature paths are detected

`@bdd-sdd-deprecated-feature-path`

### Example: Records with deprecated feature paths get a warning

- Given a record with bdd feature_file in a deprecated location
- When sdd check is run
- Then a deprecation warning is reported
