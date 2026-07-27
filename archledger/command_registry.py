"""Command registry for Archledger CLI metadata.

This module provides command metadata for the unified CLI interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CommandEffect(Enum):
    """Effect classification for commands."""

    READ_ONLY = "read_only"
    MUTATION = "mutation"
    DESTRUCTIVE = "destructive"


class CommandStability(Enum):
    """Stability classification for commands."""

    STABLE = "stable"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class CommandMetadata:
    """Metadata for a CLI command."""

    name: str
    summary: str
    effect: CommandEffect = CommandEffect.READ_ONLY
    requires_workspace: bool = True
    supports_json: bool = True
    stability: CommandStability = CommandStability.STABLE
    aliases: tuple[str, ...] = ()
    deprecated: bool = False
    replacement: str | None = None
    targeting: str | None = None


# Command registry
_COMMANDS: dict[str, CommandMetadata] = {}


def register_command(metadata: CommandMetadata) -> None:
    """Register a command with its metadata."""
    _COMMANDS[metadata.name] = metadata


def get_command_metadata(name: str) -> CommandMetadata | None:
    """Get metadata for a command by name."""
    return _COMMANDS.get(name)


def list_commands() -> list[CommandMetadata]:
    """List all registered commands."""
    return sorted(_COMMANDS.values(), key=lambda c: c.name)


def commands_payload() -> dict[str, Any]:
    """Generate the commands payload for JSON output."""
    return {
        "commands": [
            {
                "name": cmd.name,
                "summary": cmd.summary,
                "effect": cmd.effect.value,
                "requires_workspace": cmd.requires_workspace,
                "supports_json": cmd.supports_json,
                "stability": cmd.stability.value,
                "aliases": list(cmd.aliases),
                "deprecated": cmd.deprecated,
                "replacement": cmd.replacement,
                "targeting": cmd.targeting,
            }
            for cmd in list_commands()
        ]
    }


# Register migration commands
register_command(
    CommandMetadata(
        name="migrate status",
        summary="Report migration state and available migrations",
        effect=CommandEffect.READ_ONLY,
        requires_workspace=True,
        supports_json=True,
    )
)

register_command(
    CommandMetadata(
        name="migrate plan",
        summary="Create a deterministic migration plan",
        effect=CommandEffect.READ_ONLY,
        requires_workspace=True,
        supports_json=True,
    )
)

register_command(
    CommandMetadata(
        name="migrate apply",
        summary="Execute a migration plan with journaling",
        effect=CommandEffect.MUTATION,
        requires_workspace=True,
        supports_json=True,
    )
)

register_command(
    CommandMetadata(
        name="migrate recover",
        summary="Recover from an interrupted migration",
        effect=CommandEffect.MUTATION,
        requires_workspace=True,
        supports_json=True,
    )
)

register_command(
    CommandMetadata(
        name="migrate cleanup",
        summary="Remove verified legacy source after migration",
        effect=CommandEffect.DESTRUCTIVE,
        requires_workspace=True,
        supports_json=True,
    )
)

# Deprecated aliases
register_command(
    CommandMetadata(
        name="migrate project",
        summary="Inspect or apply project migration (deprecated)",
        effect=CommandEffect.READ_ONLY,
        requires_workspace=True,
        supports_json=True,
        deprecated=True,
        replacement="migrate plan project-layout",
        aliases=("migrate project --apply",),
    )
)

register_command(
    CommandMetadata(
        name="migrate ids",
        summary="Migrate IDs to Ledgercore format (deprecated)",
        effect=CommandEffect.READ_ONLY,
        requires_workspace=True,
        supports_json=True,
        deprecated=True,
        replacement="migrate plan identity-ledgercore",
    )
)

register_command(
    CommandMetadata(
        name="migrate metadata",
        summary="Migrate metadata to versioned format (deprecated)",
        effect=CommandEffect.READ_ONLY,
        requires_workspace=True,
        supports_json=True,
        deprecated=True,
        replacement="migrate plan metadata-versioned",
    )
)

# Root commands
register_command(
    CommandMetadata(
        name="commands",
        summary="List all available commands",
        effect=CommandEffect.READ_ONLY,
        requires_workspace=False,
        supports_json=True,
    )
)

register_command(
    CommandMetadata(
        name="help",
        summary="Show help for a command",
        effect=CommandEffect.READ_ONLY,
        requires_workspace=False,
        supports_json=True,
    )
)

register_command(
    CommandMetadata(
        name="info",
        summary="Show project information",
        effect=CommandEffect.READ_ONLY,
        requires_workspace=True,
        supports_json=True,
    )
)

register_command(
    CommandMetadata(
        name="next-action",
        summary="Show the next recommended action",
        effect=CommandEffect.READ_ONLY,
        requires_workspace=True,
        supports_json=True,
    )
)
