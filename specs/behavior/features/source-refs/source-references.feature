@area-source-refs @feature-source-references
Feature: Source reference normalization

  Source refs link records to implementation files with optional symbols
  and roles.

  @rule-normalization
  Rule: Source refs are normalized and validated

    @bdd-source-refs-normalize-valid
    @req-REQ-0016
    @ac-AC-0237
    Example: Valid source ref is normalized
      Given a source ref with path "src/main.py" and role "implements"
      When normalize_source_refs is called
      Then a SourceRef is returned with path "src/main.py"

    @bdd-source-refs-normalize-invalid-path
    @req-REQ-0016
    @ac-AC-0238
    Example: Non-POSIX path is rejected
      Given a source ref with path "src\\main.py"
      When normalize_source_refs is called
      Then a warning about POSIX separators is reported

    @bdd-source-refs-normalize-absolute-path
    @req-REQ-0016
    @ac-AC-0239
    Example: Absolute path is rejected
      Given a source ref with path "/src/main.py"
      When normalize_source_refs is called
      Then a warning about relative path is reported

    @bdd-source-refs-normalize-dotdot-path
    @req-REQ-0016
    @ac-AC-0240
    Example: Path with .. is rejected
      Given a source ref with path "../secret.py"
      When normalize_source_refs is called
      Then a warning about dotdot is reported

    @bdd-source-refs-normalize-invalid-role
    @req-REQ-0016
    @ac-AC-0241
    Example: Invalid role is rejected
      Given a source ref with role "invalid_role"
      When normalize_source_refs is called
      Then a warning about invalid role is reported

    @bdd-source-refs-normalize-none
    @req-REQ-0016
    @ac-AC-0242
    Example: None source refs returns empty tuple
      Given a None source_refs value
      When normalize_source_refs is called
      Then an empty tuple is returned

    @bdd-source-refs-normalize-missing-file
    @req-REQ-0016
    @ac-AC-0243
    Example: Missing file produces a warning
      Given a source ref with path "nonexistent.py"
      When normalize_source_refs is called with require_exists True
      Then a warning about missing file is reported

  @rule-path-validation
  Rule: Relative POSIX path validation catches common errors

    @bdd-source-refs-validate-posix
    @req-REQ-0016
    @ac-AC-0244
    Example: Backslash separators are rejected
      Given a path "src\\main.py"
      When validate_relative_posix_path is called
      Then a RelativePosixPathError with kind "posix" is raised

    @bdd-source-refs-validate-relative
    @req-REQ-0016
    @ac-AC-0245
    Example: Absolute paths are rejected
      Given a path "/src/main.py"
      When validate_relative_posix_path is called
      Then a RelativePosixPathError with kind "relative" is raised

    @bdd-source-refs-validate-dotdot
    @req-REQ-0016
    @ac-AC-0246
    Example: Parent traversal is rejected
      Given a path "../secret.py"
      When validate_relative_posix_path is called
      Then a RelativePosixPathError with kind "dotdot" is raised

    @bdd-source-refs-validate-empty
    @req-REQ-0016
    @ac-AC-0247
    Example: Empty path is rejected
      Given a path ""
      When validate_relative_posix_path is called
      Then a RelativePosixPathError with kind "empty" is raised
