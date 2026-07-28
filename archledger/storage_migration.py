"""Compatibility adapter for the retired Archledger storage migration API.

New code must use ``archledger.migrations.storage_layout``.  The old module is
kept as a narrow forwarding surface so downstream imports fail safe while all
planning and execution remain in the canonical migration registry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from archledger.migrations.storage_layout import StorageLayoutHandler


def plan_storage_migration(
    start: Path,
    *,
    target_storage: str = "project",
    target_external_root: str | None = None,
) -> Any:
    """Forward to the canonical storage-layout handler."""
    return StorageLayoutHandler().plan(
        start,
        {
            "storage": target_storage,
            "external_root": target_external_root,
        },
    )


def apply_storage_migration(
    plan: Any,
    *,
    reason: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Forward a canonical plan to the registered handler."""
    root = plan.project.root if plan.project else Path.cwd()
    return StorageLayoutHandler().apply(
        root,
        plan,
        dry_run=dry_run,
        reason=reason,
    )


__all__ = ["apply_storage_migration", "plan_storage_migration"]
