@area-repository @feature-skill-file
Feature: Skill file generation

  The skill file provides agent instructions for working with archledger
  projects.

  @rule-existence
  Rule: Skill file exists and is valid

    @bdd-skill-file-exists
    @req-REQ-0014
    @ac-AC-0222
    Example: Skill file is present in the project
      Given an archledger project
      When the skill file path is checked
      Then the skill file exists

    @bdd-skill-file-mentions-formats
    @req-REQ-0014
    @ac-AC-0223
    Example: Skill file mentions supported formats
      Given the skill file
      When the content is read
      Then it mentions both markdown and asciidoc

    @bdd-skill-file-instructs-read
    @req-REQ-0014
    @ac-AC-0224
    Example: Skill file instructs reading without export
      Given the skill file
      When the content is read
      Then it instructs to read without export

    @bdd-skill-file-no-legacy-markdown
    @req-REQ-0014
    @ac-AC-0225
    Example: Skill file does not reference legacy markdown export
      Given the skill file
      When the content is read
      Then it does not call markdown legacy
