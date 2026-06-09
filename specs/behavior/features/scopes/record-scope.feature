@area-scopes @feature-record-scope
Feature: Record scope normalization and matching

  Scope declares which addon, addon group, integration, subsystem, or
  whole monorepo a record applies to.

  @rule-normalization
  Rule: Scope is normalized from front-matter metadata

    @bdd-scope-normalize-valid
    Example: Valid scope is normalized without errors
      Given a scope with kind "addon", name "crm", applies_to ["addons/crm/"]
      When normalize_scope is called
      Then a RecordScope is returned with no warnings

    @bdd-scope-normalize-invalid-kind
    Example: Invalid scope kind is rejected
      Given a scope with kind "invalid"
      When normalize_scope is called
      Then an error about invalid kind is returned

    @bdd-scope-normalize-missing-name
    Example: Missing scope name is rejected
      Given a scope with kind "addon" and no name
      When normalize_scope is called
      Then an error about missing name is returned

    @bdd-scope-normalize-empty-applies-to
    Example: Empty applies_to is rejected
      Given a scope with empty applies_to list
      When normalize_scope is called
      Then an error about empty applies_to is returned

    @bdd-scope-normalize-lifecycle
    Example: Valid lifecycle values are accepted
      Given a scope with lifecycle "deprecated"
      When normalize_scope is called
      Then a RecordScope is returned with lifecycle "deprecated"

    @bdd-scope-normalize-invalid-lifecycle
    Example: Invalid lifecycle is rejected
      Given a scope with lifecycle "invalid"
      When normalize_scope is called
      Then an error about invalid lifecycle is returned

    @bdd-scope-normalize-none
    Example: None scope returns None without errors
      Given a None scope value
      When normalize_scope is called
      Then None is returned with no warnings

  @rule-matching
  Rule: Scope matching determines if a path falls within scope

    @bdd-scope-matches-directory
    Example: Path under applies_to directory matches
      Given a scope with applies_to ["addons/crm/"]
      When scope_matches_path is called with "addons/crm/models/test.py"
      Then the result is True

    @bdd-scope-matches-exact-file
    Example: Exact file path matches
      Given a scope with applies_to ["config/settings.yaml"]
      When scope_matches_path is called with "config/settings.yaml"
      Then the result is True

    @bdd-scope-excludes-path
    Example: Excluded path does not match
      Given a scope with applies_to ["addons/"] and excludes ["addons/test/"]
      When scope_matches_path is called with "addons/test/foo.py"
      Then the result is False

    @bdd-scope-no-match
    Example: Path outside scope does not match
      Given a scope with applies_to ["addons/crm/"]
      When scope_matches_path is called with "addons/sale/models/test.py"
      Then the result is False
