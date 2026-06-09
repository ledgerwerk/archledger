@area-records @feature-record-templates
Feature: Record templates

  Each record type has a Jinja2 template for generating initial content.

  @rule-templates
  Rule: All record types have bundled templates

    @bdd-templates-bundled
    Example: All record type templates are bundled
      Given the RECORD_TYPES registry
      When each template_basename is checked
      Then a corresponding .md.j2 template exists

    @bdd-templates-registry-covers-all
    Example: Registry maps cover all record types
      Given RECORD_TYPE_TO_DIR, RECORD_TYPE_TO_DEFAULT_SECTION, RECORD_TYPE_TO_TEMPLATE
      When all keys are compared
      Then all registries have the same keys as RECORD_TYPES

    @bdd-templates-legacy-maps
    Example: Legacy maps are preserved for backward compatibility
      Given the RECORD_TYPE_TO_DIR mapping
      When all entries are checked
      Then each record type has a directory mapping
