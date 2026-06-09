@area-source-refs @feature-source-references
Feature: Source reference normalization

  Source refs link records to implementation files with optional symbols
  and roles.

  @rule-normalization
  Rule: Source refs are normalized and validated

    @bdd-source-refs-normalize-valid
    Example: Valid source ref is normalized
      Given a source ref with path "src/main.py" and role "implements"
      When normalize_source_refs is called
      Then a SourceRef is returned with path "src/main.py"

    @bdd-source-refs-normalize-invalid-path
    Example: Non-POSIX path is rejected
      Given a source ref with path "src\\main.py"
      When normalize_source_refs is called
      Then a warning about POSIX separators is reported

    @bdd-source-refs-normalize-absolute-path
    Example: Absolute path is rejected
      Given a source ref with path "/src/main.py"
      When normalize_source_refs is called
      Then a warning about relative path is reported

    @bdd-source-refs-normalize-dotdot-path
    Example: Path with .. is rejected
      Given a source ref with path "../secret.py"
      When normalize_source_refs is called
      Then a warning about dotdot is reported

    @bdd-source-refs-normalize-invalid-role
    Example: Invalid role is rejected
      Given a source ref with role "invalid_role"
      When normalize_source_refs is called
      Then a warning about invalid role is reported

    @bdd-source-refs-normalize-none
    Example: None source refs returns empty tuple
      Given a None source_refs value
      When normalize_source_refs is called
      Then an empty tuple is returned

    @bdd-source-refs-normalize-missing-file
    Example: Missing file produces a warning
      Given a source ref with path "nonexistent.py"
      When normalize_source_refs is called with require_exists True
      Then a warning about missing file is reported

  @rule-path-validation
  Rule: Relative POSIX path validation catches common errors

    @bdd-source-refs-validate-posix
    Example: Backslash separators are rejected
      Given a path "src\\main.py"
      When validate_relative_posix_path is called
      Then a RelativePosixPathError with kind "posix" is raised

    @bdd-source-refs-validate-relative
    Example: Absolute paths are rejected
      Given a path "/src/main.py"
      When validate_relative_posix_path is called
      Then a RelativePosixPathError with kind "relative" is raised

    @bdd-source-refs-validate-dotdot
    Example: Parent traversal is rejected
      Given a path "../secret.py"
      When validate_relative_posix_path is called
      Then a RelativePosixPathError with kind "dotdot" is raised

    @bdd-source-refs-validate-empty
    Example: Empty path is rejected
      Given a path ""
      When validate_relative_posix_path is called
      Then a RelativePosixPathError with kind "empty" is raised
