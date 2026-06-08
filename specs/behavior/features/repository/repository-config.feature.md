`@area-repository` `@feature-repository-config`

# Feature: Repository configuration round-trip

Project configuration is loaded, validated, and rendered back to TOML
format without data loss.

`@rule-roundtrip`

## Rule: Config round-trip preserves all settings

`@bdd-config-roundtrip-markdown`

### Example: Default markdown config round-trips correctly

- Given a default markdown project config
- When the config is rendered to TOML and parsed back
- Then all settings are preserved

`@bdd-config-roundtrip-asciidoc`

### Example: Default asciidoc config round-trips correctly

- Given a default asciidoc project config
- When the config is rendered to TOML and parsed back
- Then all settings are preserved

`@rule-v2-config`

## Rule: V2 config supports new build and skill keys

`@bdd-config-v2-build-keys`

### Example: V2 config supports build_arc42 settings

- Given a v2 config with build_arc42 settings
- When the config is parsed
- Then the build_arc42 settings are accessible

`@bdd-config-v2-skill-keys`

### Example: V2 config supports skill file settings

- Given a v2 config with skill settings
- When the config is parsed
- Then the skill settings are accessible

`@rule-archledger-dir`

## Rule: Archledger directory path is resolved correctly

`@bdd-config-relative-dir`

### Example: Relative archledger dir is resolved to config path

- Given a config with relative archledger_dir
- When paths are resolved
- Then archledger_dir is relative to config_path
