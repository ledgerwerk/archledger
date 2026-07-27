"""Migration handler registry for Archledger.

This module provides the handler protocol and registration system for named migrations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from archledger.migrations.models import (
    ArchledgerMigrationPlan,
    MigrationCapabilities,
)


@runtime_checkable
class ArchledgerMigrationHandler(Protocol):
    """Protocol for migration handlers."""

    name: str
    summary: str
    capabilities: MigrationCapabilities

    def status(self, root: Path) -> dict[str, Any]:
        """Report migration-specific status."""
        ...

    def plan(self, root: Path, options: dict[str, Any]) -> ArchledgerMigrationPlan:
        """Create a deterministic migration plan."""
        ...

    def apply(
        self,
        root: Path,
        plan: ArchledgerMigrationPlan,
        *,
        dry_run: bool,
        reason: str,
    ) -> dict[str, Any]:
        """Execute a migration plan."""
        ...

    def recover(self, root: Path, journal: Path, *, dry_run: bool) -> dict[str, Any]:
        """Recover from an interrupted migration."""
        ...

    def cleanup(
        self,
        root: Path,
        *,
        dry_run: bool,
        yes: bool,
        reason: str,
    ) -> dict[str, Any]:
        """Remove verified legacy source after migration."""
        ...


# Handler registry
_HANDLERS: dict[str, ArchledgerMigrationHandler] = {}


def register_handler(handler: ArchledgerMigrationHandler) -> None:
    """Register a migration handler."""
    _HANDLERS[handler.name] = handler


def get_handler(name: str) -> ArchledgerMigrationHandler | None:
    """Get a handler by migration name."""
    return _HANDLERS.get(name)


def list_handlers() -> list[ArchledgerMigrationHandler]:
    """List all registered handlers."""
    return list(_HANDLERS.values())


def get_handler_names() -> list[str]:
    """Get all registered handler names."""
    return sorted(_HANDLERS.keys())


def has_handler(name: str) -> bool:
    """Check if a handler is registered."""
    return name in _HANDLERS
