# Behavior specifications

This directory is managed by SpecMason.

> SpecWeave was removed; the workspace now uses SpecMason for behavior-spec
> validation, coverage, and review.

Feature files live under:

```text
features/<area>/<feature>.feature
```

Identity rules:

- scenarios are identified by their `@req-REQ-NNNN` and `@ac-AC-NNNN` tag pair;
- scenario titles are not identity; the tag pair is;
- do not infer identity from `@bdd-*` tags, file names, or test names.

Use:

```bash
specmason check
specmason review
specmason coverage --view both --show gaps
specmason create-gherkin --from requirements/manifest.json
```

Rules:

- keep one feature per file;
- group feature files by area;
- every `Example:` block must carry both `@req-REQ-NNNN` and `@ac-AC-NNNN` tags.
