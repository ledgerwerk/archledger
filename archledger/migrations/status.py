"""Read-only migration status backed by structural Ledgercore inspection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from archledger.ledgercore_backend import inspect_storage_migration
from archledger.migrations.models import MigrationState, MigrationStatusReport
from archledger.migrations.registry import get_handler_names


def evaluate_migration_status(root: Path) -> MigrationStatusReport:
    """Evaluate migration state without creating directories or mutating files."""
    from archledger.project_context import classify_project_state

    state = classify_project_state(root)
    available = get_handler_names()
    completed: list[str] = []
    pending: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    journals = _inspect_journals(root / ".ledger" / "migrations")

    if state in {"uninitialized", "invalid"}:
        ledger = root / ".ledger"
        arch = ledger / "archledger"
        if (
            ledger.exists()
            and (ledger / "ledger.toml").exists()
            and arch.exists()
            and (arch / "config.toml").exists()
        ):
            migration_state = MigrationState.CANONICAL_READY
            completed = _find_completed_migrations(arch / "migrations")
            pending = [name for name in available if name not in completed]
        else:
            migration_state = MigrationState.UNINITIALIZED
            pending = list(available)
    elif state == "legacy":
        migration_state = MigrationState.LEGACY
        pending = list(available)
    elif state == "canonical":
        arch = root / ".ledger" / "archledger"
        if arch.exists() and (arch / "config.toml").exists():
            migration_state = MigrationState.CANONICAL_READY
            completed = _find_completed_migrations(arch / "migrations")
            pending = [name for name in available if name not in completed]
        else:
            migration_state = MigrationState.MIGRATION_REQUIRED
            pending = list(available)
    elif state == "partial":
        migration_state = MigrationState.PARTIAL
        blockers.append("Partial project state detected")
        pending = list(available)
    else:
        migration_state = MigrationState.UNINITIALIZED
        pending = list(available)

    for journal in journals:
        phase = journal.get("phase")
        capability = journal.get("recovery_capability")
        if journal.get("valid") is False:
            blockers.append(f"Invalid migration journal: {journal['path']}")
        elif phase not in {"complete", "committed", "rolled-back"}:
            migration_state = MigrationState.RECOVERY_REQUIRED
            blockers.append(
                f"Migration journal requires attention: {journal['path']} ({phase})"
            )
        elif capability == "manual-intervention":
            warnings.append(
                "Completed journal inspected with manual recovery capability: "
                f"{journal['path']}"
            )

    archledger_toml = root / ".archledger.toml"
    archledger_dir = root / ".archledger"
    if (
        archledger_toml.exists() or archledger_dir.exists()
    ) and migration_state == MigrationState.CANONICAL_READY:
        migration_state = MigrationState.COMPLETED_WITH_LEGACY
        warnings.append("Legacy source still exists; run cleanup to remove")

    return MigrationStatusReport(
        state=migration_state,
        available_migrations=tuple(available),
        completed_migrations=tuple(completed),
        pending_migrations=tuple(pending),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        recommended_next=_recommend_next_command(migration_state, pending),
        journals=tuple(journals),
    )


def _find_completed_migrations(receipts_dir: Path) -> list[str]:
    completed: list[str] = []
    if not receipts_dir.exists():
        return completed
    for receipt_file in receipts_dir.glob("*.json"):
        try:
            data = json.loads(receipt_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        migration_name = data.get("migration")
        if isinstance(migration_name, str):
            completed.append(migration_name)
    return sorted(set(completed))


def _inspect_journals(migrations_dir: Path) -> list[dict[str, Any]]:
    """Inspect journal structure; never infer lifecycle from text fragments."""
    if not migrations_dir.is_dir():
        return []
    journals: list[dict[str, Any]] = []
    for journal_path in sorted(migrations_dir.glob("*.toml")):
        try:
            journal = inspect_storage_migration(journal_path)
        except Exception as exc:
            journals.append(
                {
                    "path": str(journal_path),
                    "valid": False,
                    "error": str(exc),
                    "recovery_capability": "manual-intervention",
                }
            )
            continue
        journals.append(
            {
                "path": str(journal_path),
                "valid": True,
                "schema_version": journal.schema_version,
                "migration_id": journal.migration_id,
                "project_uuid": journal.project_uuid,
                "phase": journal.phase,
                "items": len(journal.items),
                "items_completed": journal.items_completed,
                "source_removed": journal.source_removed,
                "recovery_capability": journal.recovery_capability,
                "error": journal.error,
            }
        )
    return journals


def _recommend_next_command(state: MigrationState, pending: list[str]) -> str | None:
    if state == MigrationState.UNINITIALIZED:
        return None
    if state == MigrationState.RECOVERY_REQUIRED:
        return "archledger migrate recover --journal <path>"
    if state == MigrationState.LEGACY and pending:
        return f"archledger migrate plan {pending[0]}"
    if state == MigrationState.COMPLETED_WITH_LEGACY:
        return "archledger migrate cleanup project-layout --dry-run"
    if state == MigrationState.CANONICAL_READY and pending:
        return f"archledger migrate plan {pending[0]}"
    return None
