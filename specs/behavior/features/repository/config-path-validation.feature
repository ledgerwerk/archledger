@area-repository @feature-config-path-validation
Feature: Configuration version and path validation

  # Project configuration parsing must support current versioned settings while
  # rejecting path traversal, unsupported renderers, unknown output formats, and
  # boolean values in integer fields.

  @rule-config-version-support
  Rule: Versioned configuration fields are parsed explicitly

    @bdd-config-v3-source-extensions
    Example: V3 config supports source format extensions
      Given a v3 config with markdown and asciidoc source extensions
      When the config is parsed
      Then the configured extensions are preserved

    @bdd-config-v4-source-schema-version
    Example: V4 config supports source schema version
      Given a v4 config with source schema version
      When the config is parsed
      Then the source schema version is available

    @bdd-config-v5-tracking-settings
    Example: V5 config supports tracking settings
      Given a v5 config with tracking include and exclude rules
      When the config is parsed
      Then the tracking settings are available

    @bdd-config-v6-id-format
    Example: V6 config supports ID prefix and width
      Given a v6 config with ids prefix and width
      When the config is parsed
      Then the ID format settings are available

    @bdd-config-v7-id-segments
    Example: V7 config supports ID segment mode and segment map
      Given a v7 config with id_segment_mode type
      When the config is parsed
      Then the segment mode and segment map are available

  @rule-path-safety
  Rule: Configured paths stay within their allowed roots

    @bdd-config-tracking-state-inside-archledger-dir
    Example: Tracking state file must stay inside the archledger directory
      Given a config with tracking state file outside the archledger directory
      When project paths are resolved
      Then a config error is raised

    @bdd-config-build-output-dir-inside-workspace
    Example: Build output dir must stay inside workspace root
      Given a config with build output dir containing parent traversal
      When project paths are resolved
      Then a config error is raised

    @bdd-config-build-default-output-inside-output-dir
    Example: Build default output must stay inside output dir
      Given a config with default output outside the build output dir
      When project paths are resolved
      Then a config error is raised

    @bdd-config-build-output-dir-relative-root
    Example: Build output dir is relative to workspace root
      Given a config with relative build output dir docs
      When project paths are resolved
      Then build output paths are resolved under the workspace root

  @rule-output-validation
  Rule: Build output entries are validated before use

    @bdd-config-default-output-extension-matches-format
    Example: Default output extension must match default format
      Given a config with default format html and default output architecture.pdf
      When the config is parsed
      Then a config error is raised

    @bdd-config-build-outputs-reject-unknown-format
    Example: Build outputs reject unknown formats
      Given a config with build output format unknown
      When the config is parsed
      Then a config error is raised

    @bdd-config-build-outputs-validate-settings
    Example: Per-output build settings are validated
      Given a config with a named build output
      When the config is parsed
      Then enabled state, format, and path are validated

  @rule-type-strictness
  Rule: Ambiguous config values are rejected

    @bdd-config-version-bool-rejected
    Example: Boolean config version is rejected
      Given a config with version set to true
      When the config is parsed
      Then a config error is raised

    @bdd-config-integer-bool-rejected
    Example: Boolean integer-like fields are rejected
      Given a config with id width set to true
      When the config is parsed
      Then a config error is raised

    @bdd-config-kroki-renderer-rejected
    Example: Unsupported Kroki renderer is rejected
      Given a config that selects Kroki as diagram renderer
      When the config is parsed
      Then a config error is raised

    @bdd-config-invalid-segment-value-rejected
    Example: Invalid ID segment values are rejected
      Given a config with an invalid segment name
      When the config is parsed
      Then a config error is raised
