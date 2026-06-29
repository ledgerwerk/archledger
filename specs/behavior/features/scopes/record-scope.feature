@area-scopes @feature-record-scope
Feature: Record scope normalization and matching

  Scope declares which addon, addon group, integration, subsystem, or
  whole monorepo a record applies to.

  @rule-normalization
  Rule: Scope is normalized from front-matter metadata

    @bdd-scope-normalize-valid
    @req-REQ-0015
    @ac-AC-0226
    Example: Valid scope is normalized without errors
      Given a scope with kind "addon", name "crm", applies_to ["addons/crm/"]
      When normalize_scope is called
      Then a RecordScope is returned with no warnings

    @bdd-scope-normalize-invalid-kind
    @req-REQ-0015
    @ac-AC-0227
    Example: Invalid scope kind is rejected
      Given a scope with kind "invalid"
      When normalize_scope is called
      Then an error about invalid kind is returned

    @bdd-scope-normalize-missing-name
    @req-REQ-0015
    @ac-AC-0228
    Example: Missing scope name is rejected
      Given a scope with kind "addon" and no name
      When normalize_scope is called
      Then an error about missing name is returned

    @bdd-scope-normalize-empty-applies-to
    @req-REQ-0015
    @ac-AC-0229
    Example: Empty applies_to is rejected
      Given a scope with empty applies_to list
      When normalize_scope is called
      Then an error about empty applies_to is returned

    @bdd-scope-normalize-lifecycle
    @req-REQ-0015
    @ac-AC-0230
    Example: Valid lifecycle values are accepted
      Given a scope with lifecycle "deprecated"
      When normalize_scope is called
      Then a RecordScope is returned with lifecycle "deprecated"

    @bdd-scope-normalize-invalid-lifecycle
    @req-REQ-0015
    @ac-AC-0231
    Example: Invalid lifecycle is rejected
      Given a scope with lifecycle "invalid"
      When normalize_scope is called
      Then an error about invalid lifecycle is returned

    @bdd-scope-normalize-none
    @req-REQ-0015
    @ac-AC-0232
    Example: None scope returns None without errors
      Given a None scope value
      When normalize_scope is called
      Then None is returned with no warnings

  @rule-matching
  Rule: Scope matching determines if a path falls within scope

    @bdd-scope-matches-directory
    @req-REQ-0015
    @ac-AC-0233
    Example: Path under applies_to directory matches
      Given a scope with applies_to ["addons/crm/"]
      When scope_matches_path is called with "addons/crm/models/test.py"
      Then the result is True

    @bdd-scope-matches-exact-file
    @req-REQ-0015
    @ac-AC-0234
    Example: Exact file path matches
      Given a scope with applies_to ["config/settings.yaml"]
      When scope_matches_path is called with "config/settings.yaml"
      Then the result is True

    @bdd-scope-excludes-path
    @req-REQ-0015
    @ac-AC-0235
    Example: Excluded path does not match
      Given a scope with applies_to ["addons/"] and excludes ["addons/test/"]
      When scope_matches_path is called with "addons/test/foo.py"
      Then the result is False

    @bdd-scope-no-match
    @req-REQ-0015
    @ac-AC-0236
    Example: Path outside scope does not match
      Given a scope with applies_to ["addons/crm/"]
      When scope_matches_path is called with "addons/sale/models/test.py"
      Then the result is False
