"""Migration status reporting for Archledger.

This module provides read-only status reporting for migration state.
"""

from __future__ import annotations

import json
from pathlib import Path

from archledger.migrations.models import (
    MigrationState,
    MigrationStatusReport,
)
from archledger.migrations.registry import get_handler_names


def evaluate_migration_status(root: Path) -> MigrationStatusReport:
    """Evaluate the current migration status for a project.

    This is read-only and must not create .ledger/ or modify any files.
    """
    from archledger.project_context import classify_project_state

    state = classify_project_state(root)
    available = get_handler_names()
    completed: list[str] = []
    pending: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []

    # Determine state based on project classification
    if state == "uninitialized" or state == "invalid":
        # Check if .ledger exists with archledger config (canonical ready)
        ledger = root / ".ledger"
        arch = ledger / "archledger"
        if (
            ledger.exists()
            and (ledger / "ledger.toml").exists()
            and arch.exists()
            and (arch / "config.toml").exists()
        ):
            migration_state = MigrationState.CANONICAL_READY
            # Check for completed receipts
            receipts_dir = arch / "migrations"
            if receipts_dir.exists():
                completed = _find_completed_migrations(receipts_dir)
            pending = [m for m in available if m not in completed]
        else:
            migration_state = MigrationState.UNINITIALIZED
            pending = list(available)
    elif state == "legacy":
        migration_state = MigrationState.LEGACY
        pending = list(available)
    elif state == "canonical":
        # Check if already migrated
        ledger = root / ".ledger"
        arch = ledger / "archledger"
        if arch.exists() and (arch / "config.toml").exists():
            migration_state = MigrationState.CANONICAL_READY
            # Check for completed receipts
            receipts_dir = arch / "migrations"
            if receipts_dir.exists():
                completed = _find_completed_migrations(receipts_dir)
            pending = [m for m in available if m not in completed]
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

    # Check for incomplete journals (recovery required)
    ledger = root / ".ledger"
    migrations_dir = ledger / "migrations"
    if migrations_dir.exists():
        incomplete = _find_incomplete_journals(migrations_dir)
        if incomplete:
            migration_state = MigrationState.RECOVERY_REQUIRED
            blockers.append(f"Incomplete migration journals: {', '.join(incomplete)}")

    # Check for legacy source preserved
    archledger_toml = root / ".archledger.toml"
    archledger_dir = root / ".archledger"
    if archledger_toml.exists() or archledger_dir.exists():
        if migration_state == MigrationState.CANONICAL_READY:
            migration_state = MigrationState.COMPLETED_WITH_LEGACY
            warnings.append("Legacy source still exists; run cleanup to remove")

    recommended_next = _recommend_next_command(migration_state, pending)

    return MigrationStatusReport(
        state=migration_state,
        available_migrations=tuple(available),
        completed_migrations=tuple(completed),
        pending_migrations=tuple(pending),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        recommended_next=recommended_next,
    )


def _find_completed_migrations(receipts_dir: Path) -> list[str]:
    """Find completed migrations from receipts."""
    completed = []
    for receipt_file in receipts_dir.glob("*.json"):
        try:
            data = json.loads(receipt_file.read_text())
            migration_name = data.get("migration")
            if migration_name:
                completed.append(migration_name)
        except (json.JSONDecodeError, KeyError):
            continue
    return completed


def _find_incomplete_journals(migrations_dir: Path) -> list[str]:
    """Find incomplete migration journals."""
    incomplete = []
    for journal_file in migrations_dir.glob("*.toml"):
        try:
            content = journal_file.read_text()
            if "status = " in content and "completed" not in content:
                incomplete.append(journal_file.stem)
        except Exception:
            incomplete.append(journal_file.stem)
    return incomplete


def _recommend_next_command(state: MigrationState, pending: list[str]) -> str | None:
    """Recommend the next command based on state."""
    if state == MigrationState.UNINITIALIZED:
        return None
    if state == MigrationState.RECOVERY_REQUIRED:
        return "archledger migrate recover --journal <path>"
    if state == MigrationState.LEGACY:
        if pending:
            return f"archledger migrate plan {pending[0]}"
    if state == MigrationState.COMPLETED_WITH_LEGACY:
        return "archledger migrate cleanup project-layout --dry-run"
    if state == MigrationState.CANONICAL_READY and pending:
        return f"archledger migrate plan {pending[0]}"
    return None
