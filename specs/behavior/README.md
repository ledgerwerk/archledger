# Behavior specifications

This directory is managed by SpecWeave.

Canonical feature files live under:

```text
features/<area>/<feature>.feature.md
```

Classic `.feature` files remain fully supported.

Use:

```bash
specweave doctor
specweave review specs
specweave create gherkin --from-tests tests
```

Rules:

- keep one feature per file;
- group feature files by area;
- use stable `@bdd-*` tags for scenarios/examples;
- use `@ac-*` tags only when validating a task acceptance criterion;
- do not rely on scenario titles as validation keys.
