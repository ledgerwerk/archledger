@area-test-refs @feature-test-references
Feature: Test reference normalization

  Test refs link records to executable test files or test node IDs.

  @rule-normalization
  Rule: Test refs are normalized from front-matter metadata

    @bdd-test-refs-normalize-compact
    Example: Compact string form is parsed correctly
      Given a test_ref "tests/test_main.py::test_func"
      When normalize_test_refs is called
      Then a TestRef is returned with path "tests/test_main.py" and nodeid "test_func"

    @bdd-test-refs-normalize-dict
    Example: Dict form is normalized correctly
      Given a test_ref with path "tests/test_main.py" and nodeid "test_func"
      When normalize_test_refs is called
      Then a TestRef is returned with path and nodeid

    @bdd-test-refs-normalize-invalid-path
    Example: Non-POSIX path is rejected
      Given a test_ref with path "tests\\test.py"
      When normalize_test_refs is called
      Then a warning about POSIX path is reported

    @bdd-test-refs-normalize-missing-file
    Example: Missing test file produces a warning
      Given a test_ref with path "tests/nonexistent.py"
      When normalize_test_refs is called
      Then a warning about missing path is reported

    @bdd-test-refs-normalize-none
    Example: None test refs returns empty tuple
      Given a None test_refs value
      When normalize_test_refs is called
      Then an empty tuple is returned

    @bdd-test-refs-normalize-empty-entry
    Example: Empty string entry is rejected
      Given a test_ref ""
      When normalize_test_refs is called
      Then a warning about non-empty entry is reported

    @bdd-test-refs-normalize-role
    Example: Test ref role is preserved
      Given a test_ref with role "validates"
      When normalize_test_refs is called
      Then the TestRef role is "validates"
