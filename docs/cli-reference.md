<!-- Generated from archledger.cli_inventory.COMMAND_INVENTORY. Do not edit by hand. -->

# CLI reference

The command inventory is the source for `archledger commands`, nested
`archledger help`, and this reference. Compatibility aliases remain supported
and emit structured deprecation warnings.

| Command                  | Effect          | Summary                                        |
| ------------------------ | --------------- | ---------------------------------------------- |
| `init`                   | workspace-write | Initialize an Archledger workspace.            |
| `status`                 | read            | Show current Archledger status.                |
| `info`                   | read            | Show resolved project and storage details.     |
| `commands`               | read            | List the shared command inventory.             |
| `help`                   | read            | Show inventory-driven command help.            |
| `next-action`            | read            | Recommend the next safe read-only action.      |
| `doctor`                 | read            | Inspect Archledger health.                     |
| `check`                  | read            | Validate Archledger records.                   |
| `build`                  | read            | Build the architecture document.               |
| `storage where`          | read            | Show effective storage topology.               |
| `storage validate`       | read            | Validate storage topology and bindings.        |
| `storage set`            | workspace-write | Set storage topology without moving data.      |
| `storage clear-override` | workspace-write | Clear local storage topology override.         |
| `migrate status`         | read            | Report migration state and recovery needs.     |
| `migrate plan`           | read            | Create a deterministic migration plan.         |
| `migrate apply`          | workspace-write | Execute a reviewed migration plan.             |
| `migrate recover`        | workspace-write | Analyze or recover an interrupted migration.   |
| `migrate cleanup`        | workspace-write | Remove verified legacy source after migration. |
| `record create`          | ledger-write    | Create one architecture record.                |
| `record list`            | read            | List architecture records.                     |
| `record show`            | read            | Show one architecture record.                  |
| `record read`            | read            | Read one architecture record.                  |
| `record set-status`      | ledger-write    | Set record status and reason.                  |
| `record archive`         | ledger-write    | Archive one architecture record.               |
| `record meta set`        | ledger-write    | Set typed record metadata.                     |
| `record body append`     | ledger-write    | Append to a record body.                       |
| `record body set`        | ledger-write    | Replace a record body.                         |
| `record export`          | read            | Export one complete record.                    |
| `record apply`           | ledger-write    | Apply a complete record document.              |
| `ref add`                | ledger-write    | Add a source reference.                        |
| `link add`               | ledger-write    | Add a record link.                             |
| `source changed`         | read            | Report source drift.                           |
| `source snapshot`        | workspace-write | Record a source snapshot.                      |
| `source convert`         | workspace-write | Convert source dialects.                       |
| `context`                | read            | Read focused architecture context.             |
| `trace`                  | read            | Trace architecture evidence.                   |
| `schema`                 | read            | Show published schemas.                        |
| `renumber`               | workspace-write | Inspect or apply ID renumbering.               |
| `scope list`             | read            | List record scope metadata.                    |
| `scope show`             | read            | Show record scope metadata.                    |
| `scope affected`         | read            | Show affected records.                         |
| `ac add`                 | ledger-write    | Add an inline acceptance criterion.            |
| `install`                | workspace-write | Install integration scaffolding.               |
| `profile list`           | read            | List enabled profiles.                         |
| `profile enable`         | workspace-write | Enable a profile.                              |
| `profile disable`        | workspace-write | Disable a profile.                             |
| `profile migrate`        | workspace-write | Migrate profile data.                          |
| `paths`                  | read            | Compatibility path inspection alias.           |
| `ref`                    | ledger-write    | Manage source references.                      |
| `link`                   | ledger-write    | Manage record links.                           |
| `migrate project`        | read            | Compatibility project-layout migration alias.  |
| `migrate ids`            | read            | Compatibility identity migration alias.        |
| `migrate metadata`       | read            | Compatibility metadata migration alias.        |

## Canonical syntax and compatibility aliases

| Older path         | Canonical path                     |
| ------------------ | ---------------------------------- |
| `new`              | `record create`                    |
| `list`             | `record list`                      |
| `show`             | `record show`                      |
| `read`             | `record read`                      |
| `archive`          | `record archive`                   |
| `refs add`         | `ref add`                          |
| `links add`        | `link add`                         |
| `migrate ids`      | `migrate plan identity-ledgercore` |
| `migrate metadata` | `migrate plan metadata-versioned`  |
| `migrate project`  | `migrate plan project-layout`      |
| `paths`            | `storage where`                    |

Aliases are not removed. They return the same result shape and include a
deprecation warning in both human and JSON output.
