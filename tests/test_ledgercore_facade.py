"""Contract tests for Archledger's public Ledgercore adapter boundary."""

from __future__ import annotations

import inspect

import ledgercore

from archledger.ledgercore_backend import (
    build_storage_migration_plan,
    execute_storage_migration,
    inspect_storage_migration,
    ledgercore_migration_support,
    ledgercore_version,
    migration_lock,
    recover_storage_migration,
    validate_storage_migration_plan,
)


def test_ledgercore_060_public_facade_imports() -> None:
    """Every detailed migration dependency is available from package root."""
    required = (
        "plan_storage_migration",
        "validate_storage_migration_plan",
        "execute_storage_migration",
        "inspect_storage_migration",
        "recover_storage_migration",
        "MigrationLock",
        "StorageMigrationHooks",
    )
    assert all(
        callable(getattr(ledgercore, name, None)) or hasattr(ledgercore, name)
        for name in required
    )

    assert callable(build_storage_migration_plan)
    assert callable(validate_storage_migration_plan)
    assert callable(execute_storage_migration)
    assert callable(inspect_storage_migration)
    assert callable(recover_storage_migration)
    assert callable(migration_lock)


def test_archledger_backend_uses_no_private_ledgercore_symbols() -> None:
    """The adapter delegates through the public package facade."""
    assert "ledgercore.migration" not in inspect.getsource(build_storage_migration_plan)
    assert "ledgercore.migration" not in inspect.getsource(execute_storage_migration)
    assert "ledgercore._" not in inspect.getsource(ledgercore_migration_support)


def test_supported_ledgercore_version_range() -> None:
    """The installed Ledgercore exposes a parseable supported development API."""
    version = ledgercore_version()
    assert version != "unknown"
    parts = version.split(".")
    assert len(parts) >= 2
    assert all(part.isdigit() for part in parts[:2])


def test_prototype_migration_capabilities_are_truthful() -> None:
    """Model exports alone do not advertise schema-3 execution or recovery."""
    support = ledgercore_migration_support()
    assert support.public_api
    assert support.destination_policies
    if support.version.startswith("0.6"):
        assert not support.schema3_execution
        assert not support.schema3_recovery
