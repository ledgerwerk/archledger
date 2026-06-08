`@area-bdd` `@feature-gherkin-parsing`

# Feature: Minimal Gherkin parser for archledger import

The parser handles Feature, Rule, Scenario/Example, tags, and
Given/When/Then/And/But steps. Unsupported constructs raise clear
errors rather than silently misreading.

`@rule-supported-constructs`

## Rule: Supported constructs parse correctly

`@bdd-gherkin-feature-with-rule`

### Example: Feature with Rule and multiple Scenarios

- Given a Gherkin text with a Feature header and a Rule block
- When the text contains two Scenario blocks with Given/When/Then steps
- Then both scenarios are parsed with correct names, steps, and rule name
- And feature-level tags are collected

`@bdd-gherkin-feature-without-rule`

### Example: Feature without Rule

- Given a Gherkin text with a Feature header but no Rule
- When the text contains a Scenario with Given/When/Then steps
- Then the scenario parses with an empty rule

`@bdd-gherkin-example-keyword`

### Example: Example keyword is accepted

- Given a Gherkin text using the Example keyword instead of Scenario
- When the text is parsed
- Then the example is treated identically to a Scenario

`@bdd-gherkin-tags`

### Example: Tags are applied to scenarios

- Given a Gherkin text with tags on a scenario line
- When the text is parsed
- Then the scenario carries the parsed tags

`@bdd-gherkin-and-but`

### Example: And and But append to the last step bucket

- Given a Gherkin text with And and But steps after Given/When/Then
- When the text is parsed
- Then And and But steps are appended to the preceding Given, When, or Then bucket

`@bdd-gherkin-multiple-rules`

### Example: Multiple Rule blocks preserve per-scenario rule assignment

- Given a Gherkin text with two Rule blocks each containing a Scenario
- When the text is parsed
- Then each scenario carries the rule active at its definition point

`@rule-unsupported-constructs`

## Rule: Unsupported constructs raise clear errors

`@bdd-gherkin-rejects-no-feature`

### Example: No Feature line raises GherkinSyntaxError

- Given a Gherkin text without a Feature line
- When the text is parsed
- Then a GherkinSyntaxError is raised

`@bdd-gherkin-rejects-multiple-features`

### Example: Multiple Feature lines raise GherkinSyntaxError

- Given a Gherkin text with two Feature lines
- When the text is parsed
- Then a GherkinSyntaxError is raised

`@bdd-gherkin-rejects-background`

### Example: Background raises UnsupportedGherkinError

- Given a Gherkin text with a Background block
- When the text is parsed
- Then an UnsupportedGherkinError is raised

`@bdd-gherkin-rejects-scenario-outline`

### Example: Scenario Outline raises UnsupportedGherkinError

- Given a Gherkin text with a Scenario Outline block
- When the text is parsed
- Then an UnsupportedGherkinError is raised

`@bdd-gherkin-rejects-doc-string`

### Example: Doc strings raise UnsupportedGherkinError

- Given a Gherkin text containing triple-quoted doc strings
- When the text is parsed
- Then an UnsupportedGherkinError is raised

`@bdd-gherkin-rejects-data-table`

### Example: Data tables raise UnsupportedGherkinError

- Given a Gherkin text containing pipe-delimited data tables
- When the text is parsed
- Then an UnsupportedGherkinError is raised

`@bdd-gherkin-rejects-orphan-and`

### Example: And before any Given/When/Then raises GherkinSyntaxError

- Given a Gherkin text where And appears before any Given/When/Then step
- When the text is parsed
- Then a GherkinSyntaxError is raised
