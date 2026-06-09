@area-repository @feature-repository-read
Feature: Repository read operations

  Records can be read as JSON with optional body inclusion and status
  filtering.

  @rule-read
  Rule: Read returns records in JSON format

    @bdd-repo-read-json-body
    Example: Read JSON includes record bodies when requested
      Given a workspace with a record that has body text
      When archledger read --json --include-body is run
      Then the JSON output contains the body field

    @bdd-repo-read-json-draft
    Example: Read JSON includes draft records when flag is set
      Given a workspace with a draft record
      When archledger read --json --include-draft is run
      Then the draft record appears in the output

    @bdd-repo-read-json-excludes-draft
    Example: Read JSON excludes draft records by default
      Given a workspace with only draft records
      When archledger read --json is run
      Then no records appear in the output
