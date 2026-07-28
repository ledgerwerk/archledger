"""Compatibility facade for the Ledgercore-backed command inventory."""

from archledger.cli_inventory import (
    COMMAND_INVENTORY,
    CommandMetadata,
    commands_payload,
    resolve_command,
)


def get_command_metadata(name: str) -> CommandMetadata | None:
    """Return metadata for a canonical command or alias."""
    return resolve_command(name)


def list_commands() -> list[CommandMetadata]:
    """Return all inventory entries in stable order."""
    return sorted(COMMAND_INVENTORY.entries, key=lambda item: item.path)


__all__ = [
    "CommandMetadata",
    "commands_payload",
    "get_command_metadata",
    "list_commands",
]
