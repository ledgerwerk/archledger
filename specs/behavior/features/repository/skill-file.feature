@area-repository @feature-skill-file
Feature: Skill file generation

  The skill file provides agent instructions for working with archledger
  projects.

  @rule-existence
  Rule: Skill file exists and is valid

    @bdd-skill-file-exists
    Example: Skill file is present in the project
      Given an archledger project
      When the skill file path is checked
      Then the skill file exists

    @bdd-skill-file-mentions-formats
    Example: Skill file mentions supported formats
      Given the skill file
      When the content is read
      Then it mentions both markdown and asciidoc

    @bdd-skill-file-instructs-read
    Example: Skill file instructs reading without export
      Given the skill file
      When the content is read
      Then it instructs to read without export

    @bdd-skill-file-no-legacy-markdown
    Example: Skill file does not reference legacy markdown export
      Given the skill file
      When the content is read
      Then it does not call markdown legacy
