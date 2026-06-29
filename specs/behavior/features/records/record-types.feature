@area-records @feature-record-types
Feature: Record type registry and normalization

  Architecture records have typed kinds with aliases, default sections,
  templates, and context factories.

  @rule-registry
  Rule: All record types are registered with kind, aliases, and defaults

    @bdd-records-types-complete
    @req-REQ-0012
    @ac-AC-0111
    Example: Registry covers all expected record kinds
      Given the RECORD_TYPES registry
      When all kinds are collected
      Then the set includes requirement, stakeholder, quality_goal, constraint,
      And context_interface, strategy_item, white_box, black_box, interface,
      And runtime_scenario, infrastructure, concept, adr, quality_requirement,
      And quality_scenario, risk, diagram, acceptance_criterion, glossary_term

    @bdd-records-types-aliases
    @req-REQ-0012
    @ac-AC-0112
    Example: CLI aliases map to canonical kinds
      Given the CLI_KIND_ALIASES mapping
      When "quality-goal" is looked up
      Then the canonical kind is "quality_goal"

    @bdd-records-types-default-section
    @req-REQ-0012
    @ac-AC-0113
    Example: Each type has a default section
      Given the RECORD_TYPE_TO_DEFAULT_SECTION mapping
      When "adr" is looked up
      Then the default section is "architecture_decisions"

  @rule-normalization
  Rule: Kind normalization resolves aliases and rejects unknowns

    @bdd-records-normalize-alias
    @req-REQ-0012
    @ac-AC-0114
    Example: Normalize resolves hyphenated alias
      Given a kind string "quality-goal"
      When normalize_kind is called
      Then the result is "quality_goal"

    @bdd-records-normalize-rejects-unknown
    @req-REQ-0012
    @ac-AC-0115
    Example: Normalize rejects unknown kind
      Given a kind string "unknown_thing"
      When normalize_kind is called
      Then a ValueError is raised
