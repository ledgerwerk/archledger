"""Receipt management for Archledger migrations.

This module handles writing and reading migration receipts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from archledger.migrations.models import ArchledgerMigrationReceipt


def write_receipt(
    receipt: ArchledgerMigrationReceipt,
    migrations_dir: Path,
) -> Path:
    """Write a receipt to the migrations directory.

    Args:
        receipt: The receipt to write.
        migrations_dir: The directory to write receipts to.

    Returns:
        The path to the written receipt.
    """
    migrations_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = migrations_dir / f"{receipt.migration_id}.json"
    receipt_path.write_text(json.dumps(receipt.to_dict(), indent=2, sort_keys=False))
    return receipt_path


def read_receipt(receipt_path: Path) -> ArchledgerMigrationReceipt:
    """Read a receipt from a file.

    Args:
        receipt_path: The path to the receipt file.

    Returns:
        The receipt.
    """
    data = json.loads(receipt_path.read_text())
    return ArchledgerMigrationReceipt(
        migration_id=data["migration_id"],
        migration=data["migration"],
        completed_at=data["completed_at"],
        project_uuid_before=data.get("project_uuid_before"),
        project_uuid_after=data.get("project_uuid_after"),
        source_fingerprint=data["source_fingerprint"],
        canonical_fingerprint=data["canonical_fingerprint"],
        legacy_source_preserved=data["legacy_source_preserved"],
        cleanup_available=data["cleanup_available"],
        cleanup_command=data["cleanup_command"],
        copied_paths=tuple(data.get("copied_paths", [])),
        rewritten_paths=tuple(data.get("rewritten_paths", [])),
    )


def find_receipts(migrations_dir: Path) -> list[Path]:
    """Find all receipt files in a migrations directory.

    Args:
        migrations_dir: The directory to search.

    Returns:
        List of receipt file paths.
    """
    if not migrations_dir.exists():
        return []
    return sorted(migrations_dir.glob("*.json"))


def find_receipt_for_migration(
    migrations_dir: Path, migration_name: str
) -> Path | None:
    """Find a receipt for a specific migration.

    Args:
        migrations_dir: The directory to search.
        migration_name: The migration name to find.

    Returns:
        The path to the receipt, or None if not found.
    """
    for receipt_path in find_receipts(migrations_dir):
        try:
            receipt = read_receipt(receipt_path)
            if receipt.migration == migration_name:
                return receipt_path
        except (json.JSONDecodeError, KeyError):
            continue
    return None


def create_receipt(
    migration_id: str,
    migration_name: str,
    project_uuid_before: str | None,
    project_uuid_after: str | None,
    source_fingerprint: str,
    canonical_fingerprint: str,
    copied_paths: list[str],
    rewritten_paths: list[str],
) -> ArchledgerMigrationReceipt:
    """Create a new receipt.

    Args:
        migration_id: Unique ID for this migration.
        migration_name: Name of the migration.
        project_uuid_before: Project UUID before migration.
        project_uuid_after: Project UUID after migration.
        source_fingerprint: Fingerprint of the source.
        canonical_fingerprint: Fingerprint of the canonical result.
        copied_paths: Paths that were copied.
        rewritten_paths: Paths that were rewritten.

    Returns:
        A new receipt.
    """
    now = datetime.now(timezone.utc).isoformat()
    return ArchledgerMigrationReceipt(
        migration_id=migration_id,
        migration=migration_name,
        completed_at=now,
        project_uuid_before=project_uuid_before,
        project_uuid_after=project_uuid_after,
        source_fingerprint=source_fingerprint,
        canonical_fingerprint=canonical_fingerprint,
        legacy_source_preserved=True,
        cleanup_available=True,
        cleanup_command=f"archledger migrate cleanup {migration_name} --dry-run",
        copied_paths=tuple(copied_paths),
        rewritten_paths=tuple(rewritten_paths),
    )
