"""Identity-ledgercore migration handler for Archledger.

This handler migrates legacy Archledger IDs to Ledgercore local IDs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from archledger.migrations.models import (
    ArchledgerMigrationPlan,
    MigrationCapabilities,
)


class IdentityLedgercoreHandler:
    """Handler for identity-ledgercore migration."""

    name = "identity-ledgercore"
    summary = "Migrate legacy Archledger IDs to Ledgercore local IDs and global refs"
    capabilities = MigrationCapabilities(
        plan=True,
        apply=True,
        recover=True,  # completed-only initially
        cleanup=False,
        requires_legacy_state=False,
        requires_project_layout=True,
    )

    def status(self, root: Path) -> dict[str, Any]:
        """Report migration-specific status."""
        # Check if project-layout is complete
        ledger = root / ".ledger"
        arch = ledger / "archledger"
        if not (arch.exists() and (arch / "config.toml").exists()):
            return {"state": "requires-project-layout"}

        return {"state": "available"}

    def plan(self, root: Path, options: dict[str, Any]) -> ArchledgerMigrationPlan:
        """Create a deterministic migration plan."""
        # TODO: Implement planning
        raise NotImplementedError("Identity-ledgercore planning not yet implemented")

    def apply(
        self,
        root: Path,
        plan: ArchledgerMigrationPlan,
        *,
        dry_run: bool,
        reason: str,
    ) -> dict[str, Any]:
        """Execute a migration plan."""
        # TODO: Implement apply
        raise NotImplementedError("Identity-ledgercore apply not yet implemented")

    def recover(self, root: Path, journal: Path, *, dry_run: bool) -> dict[str, Any]:
        """Recover from an interrupted migration."""
        raise NotImplementedError("Identity-ledgercore recovery not yet implemented")

    def cleanup(
        self,
        root: Path,
        *,
        dry_run: bool,
        yes: bool,
        reason: str,
    ) -> dict[str, Any]:
        """Remove verified legacy source after migration."""
        raise NotImplementedError("Identity-ledgercore cleanup not supported")


# Register the handler
from archledger.migrations.registry import register_handler  # noqa: E402

register_handler(IdentityLedgercoreHandler())
