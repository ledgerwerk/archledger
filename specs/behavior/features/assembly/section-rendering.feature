@area-assembly @feature-section-rendering
Feature: Section rendering

  Section rendering assembles record data into structured arc42 sections
  with proper formatting.

  @rule-building-blocks
  Rule: Building block view renders hierarchical structure

    @bdd-section-building-block-hierarchy
    Example: Building block hierarchy omits empty fields
      Given a white_box record without fulfilled_requirements
      When building_block_hierarchy is called
      Then the output omits the fulfilled requirements section

    @bdd-section-building-block-with-fulfilled
    Example: Building block hierarchy includes fulfilled requirements when present
      Given a white_box record with fulfilled_requirements
      When building_block_hierarchy is called
      Then the output includes the fulfilled requirements

    @bdd-section-building-block-risks
    Example: Building block hierarchy includes risks when present
      Given a black_box record with risks
      When building_block_hierarchy is called
      Then the output includes the risks section

  @rule-diagrams
  Rule: Section diagrams render diagram body and caption

    @bdd-section-diagram-body
    Example: Diagram section renders diagram body
      Given a diagram record with mermaid content
      When section_diagrams is called
      Then the output contains the mermaid block

    @bdd-section-diagram-caption
    Example: Diagram section renders caption
      Given a diagram record with caption "System Overview"
      When section_diagrams is called
      Then the output contains "System Overview"

  @rule-overview-tables
  Rule: Overview sections render structured tables

    @bdd-section-requirements-overview
    Example: Requirements overview renders as a table
      Given requirement records in the introduction section
      When requirements_overview is called
      Then a table with requirement titles is produced

    @bdd-section-stakeholders-table
    Example: Stakeholders table renders contact info
      Given stakeholder records
      When stakeholders_table is called
      Then a table with stakeholder names is produced

    @bdd-section-quality-goals
    Example: Quality goals table renders priorities
      Given quality_goal records
      When quality_goals_table is called
      Then a table with goals and priorities is produced

    @bdd-section-glossary-table
    Example: Glossary table renders terms and definitions
      Given glossary_term records
      When glossary_table is called
      Then a table with terms and definitions is produced
