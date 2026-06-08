`@area-repository` `@feature-repository-init`

# Feature: Repository initialization

New archledger workspaces are initialized with config, storage metadata,
section directories, and record type directories.

`@rule-init`

## Rule: Init creates the canonical workspace structure

`@bdd-repo-init-creates-config`

### Example: Init writes archledger.toml config file

- Given an empty workspace directory
- When archledger init is run
- Then .archledger.toml is created with default settings

`@bdd-repo-init-creates-storage-meta`

### Example: Init creates storage metadata

- Given an empty workspace directory
- When archledger init is run
- Then storage-meta.json is created with schema version 2

`@bdd-repo-init-creates-sections`

### Example: Init creates all arc42 section directories

- Given an empty workspace directory
- When archledger init is run
- Then directories for all 12 arc42 sections exist

`@bdd-repo-init-creates-record-dirs`

### Example: Init creates directories for all record types

- Given an empty workspace directory
- When archledger init is run
- Then directories for requirements, stakeholders, decisions exist

`@bdd-repo-init-project-name-default`

### Example: Project name defaults to workspace basename

- Given a workspace directory named "my-project"
- When archledger init is run
- Then the config project_name is "my-project"

`@rule-status`

## Rule: Status reports workspace health

`@bdd-repo-status-counts`

### Example: Status counts sections and record directories

- Given an initialized workspace with 3 section files
- When archledger status is run
- Then sections_count is 3
