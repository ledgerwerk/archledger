"""Single Ledgercore-backed command metadata inventory."""

from __future__ import annotations

from ledgercore.cli import CommandInventory, CommandMetadata


def _entry(
    path: str,
    summary: str,
    *,
    effect: str = "read",
    requires_workspace: bool = True,
    aliases: tuple[str, ...] = (),
    deprecated: bool = False,
    replacement: str | None = None,
) -> CommandMetadata:
    return CommandMetadata(
        path=path,
        summary=summary,
        effect=effect,  # type: ignore[arg-type]
        requires_workspace=requires_workspace,
        aliases=aliases,
        deprecated=deprecated,
        replacement=replacement,
    )


COMMAND_INVENTORY = CommandInventory(
    (
        _entry("init", "Initialize an Archledger workspace.", effect="workspace-write"),
        _entry("status", "Show current Archledger status."),
        _entry("info", "Show resolved project and storage details."),
        _entry("commands", "List the shared command inventory."),
        _entry("help", "Show inventory-driven command help."),
        _entry("next-action", "Recommend the next safe read-only action."),
        _entry("doctor", "Inspect Archledger health."),
        _entry("check", "Validate Archledger records."),
        _entry("build", "Build the architecture document."),
        _entry("storage where", "Show effective storage topology."),
        _entry("storage validate", "Validate storage topology and bindings."),
        _entry(
            "storage set",
            "Set storage topology without moving data.",
            effect="workspace-write",
        ),
        _entry(
            "storage clear-override",
            "Clear local storage topology override.",
            effect="workspace-write",
        ),
        _entry("migrate status", "Report migration state and recovery needs."),
        _entry("migrate plan", "Create a deterministic migration plan."),
        _entry(
            "migrate apply",
            "Execute a reviewed migration plan.",
            effect="workspace-write",
        ),
        _entry(
            "migrate recover",
            "Analyze or recover an interrupted migration.",
            effect="workspace-write",
        ),
        _entry(
            "migrate cleanup",
            "Remove verified legacy source after migration.",
            effect="workspace-write",
        ),
        _entry(
            "record create",
            "Create one architecture record.",
            effect="ledger-write",
            aliases=("new",),
        ),
        _entry("record list", "List architecture records.", aliases=("list",)),
        _entry("record show", "Show one architecture record.", aliases=("show",)),
        _entry("record read", "Read one architecture record.", aliases=("read",)),
        _entry(
            "record set-status",
            "Set record status and reason.",
            effect="ledger-write",
            aliases=("record set",),
        ),
        _entry(
            "record archive",
            "Archive one architecture record.",
            effect="ledger-write",
            aliases=("archive",),
        ),
        _entry(
            "paths",
            "Show resolved storage paths.",
            aliases=(),
            deprecated=True,
            replacement="storage where",
        ),
        _entry(
            "ref",
            "Manage source references.",
            effect="ledger-write",
            aliases=("refs",),
            deprecated=True,
            replacement="ref",
        ),
        _entry(
            "link",
            "Manage record links.",
            effect="ledger-write",
            aliases=("links",),
            deprecated=True,
            replacement="link",
        ),
        _entry("ref add", "Add a source reference.", effect="ledger-write"),
        _entry("link add", "Add a record link.", effect="ledger-write"),
        _entry("record meta set", "Set typed record metadata.", effect="ledger-write"),
        _entry("record body append", "Append to a record body.", effect="ledger-write"),
        _entry("record body set", "Replace a record body.", effect="ledger-write"),
        _entry("record export", "Export one complete record.", effect="read"),
        _entry(
            "record apply", "Apply a complete record document.", effect="ledger-write"
        ),
        _entry("source changed", "Report source drift."),
        _entry(
            "source snapshot", "Record a source snapshot.", effect="workspace-write"
        ),
        _entry("source convert", "Convert source dialects.", effect="workspace-write"),
        _entry("context", "Read focused architecture context."),
        _entry("trace", "Trace architecture evidence."),
        _entry("schema", "Show published schemas."),
        _entry(
            "renumber", "Inspect or apply ID renumbering.", effect="workspace-write"
        ),
        _entry("scope list", "List record scope metadata."),
        _entry("scope show", "Show record scope metadata."),
        _entry("scope affected", "Show affected records."),
        _entry("ac add", "Add an inline acceptance criterion.", effect="ledger-write"),
        _entry("install", "Install integration scaffolding.", effect="workspace-write"),
        _entry("profile list", "List enabled profiles."),
        _entry("profile enable", "Enable a profile.", effect="workspace-write"),
        _entry("profile disable", "Disable a profile.", effect="workspace-write"),
        _entry("profile migrate", "Migrate profile data.", effect="workspace-write"),
        _entry(
            "migrate project",
            "Inspect or apply project layout migration.",
            deprecated=True,
            replacement="migrate plan project-layout",
        ),
        _entry(
            "migrate ids",
            "Migrate IDs to Ledgercore format.",
            deprecated=True,
            replacement="migrate plan identity-ledgercore",
        ),
        _entry(
            "migrate metadata",
            "Migrate metadata to versioned format.",
            deprecated=True,
            replacement="migrate plan metadata-versioned",
        ),
    )
)


def commands_payload() -> dict[str, object]:
    """Return the shared JSON inventory payload."""
    return {
        "commands": [
            {"name": entry.path, **entry.as_mapping()}
            for entry in COMMAND_INVENTORY.entries
        ]
    }


def resolve_command(path_or_alias: str) -> CommandMetadata | None:
    """Resolve a canonical command or compatibility alias."""
    return COMMAND_INVENTORY.resolve(path_or_alias)


def validate_inventory(registered_paths: set[str]) -> list[str]:
    """Return registration/inventory drift findings for CI and tests."""
    canonical = {entry.path for entry in COMMAND_INVENTORY.entries}
    return [
        *(
            f"registered command lacks metadata: {path}"
            for path in sorted(registered_paths - canonical)
        ),
        *(
            f"metadata command is not registered: {path}"
            for path in sorted(canonical - registered_paths)
        ),
    ]


__all__ = [
    "COMMAND_INVENTORY",
    "CommandInventory",
    "CommandMetadata",
    "commands_payload",
    "resolve_command",
    "validate_inventory",
]
