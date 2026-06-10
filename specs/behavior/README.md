# Behavior specifications

This directory is managed by SpecWeave.

Feature files live under:

```text
features/<area>/<feature>.feature
```

Generated indexes:

- `index.md` is the complete Gherkin feature and scenario list.
- `manifest.json` is the machine-readable feature manifest.
- `source-test-links.md` links scanned `archledger/` source files, feature files, and `tests/` files.

Use:

```bash
specweave doctor
specweave behavior check
specweave behavior index --features specs/behavior/features --out specs/behavior/index.md --manifest specs/behavior/manifest.json --tests-dir tests
specweave create gherkin --from-tests tests
```

Rules:

- keep one feature per file;
- group feature files by area;
- use stable `@bdd-*` tags for scenarios/examples;
- use `@ac-*` tags only when validating a task acceptance criterion;
- do not rely on scenario titles as validation keys.
