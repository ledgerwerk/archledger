from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from archledger.config.render import build_default_project_config, render_project_config
from archledger.errors import ConfigError
from archledger.ledgercore_backend import ensure_archledger_registration, initialize_archledger_bindings
from archledger.project_context import load_project_context


def _write_project(root: Path) -> str:
    project_uuid = str(uuid4())
    # Create schema-3 manifest with archledger registration.
    ensure_archledger_registration(
        root / ".ledger/ledger.toml",
        project_uuid=project_uuid,
        project_name="demo",
        data_storage="project",
    )
    # Write tool config.
    config = build_default_project_config(root, archledger_dir="data", project_uuid=project_uuid)
    config_path = root / ".ledger/archledger/config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(render_project_config(config))
    # Initialize bindings.
    initialize_archledger_bindings(
        root,
        project_uuid=project_uuid,
        project_name="demo",
        data_storage="project",
    )
    return project_uuid


def test_context_resolves_exact_repository_mount(tmp_path: Path) -> None:
    project_uuid = _write_project(tmp_path)

    context = load_project_context(tmp_path, require_initialized=False)

    assert context.project_uuid == project_uuid
    assert context.config_path == tmp_path / ".ledger/archledger/config.toml"
    assert context.data_root == tmp_path / ".ledger/archledger/data"
    assert context.build_dir == tmp_path
    assert context.active_mount_name == "data"
    assert context.mount_storage == "project"


def test_repository_mount_ignores_workspace_and_cache_environment(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path)

    context = load_project_context(
        tmp_path,
        require_initialized=False,
        environ={
            "LEDGER_WORKSPACE_ROOT": str(tmp_path / "missing-workspace"),
            "LEDGER_CACHE_ROOT": str(tmp_path / "missing-cache"),
            "LEDGER_CHECKOUT_ID": "checkout",
        },
    )

    assert context.data_root == tmp_path / ".ledger/archledger/data"


def test_legacy_locator_requires_explicit_migration(tmp_path: Path) -> None:
    """Legacy .archledger.toml without a schema-3 manifest raises a ledgercore error.
    The CLI catches this case and shows an ARCHLEDGER_MIGRATION_REQUIRED message.
    """
    (tmp_path / ".archledger.toml").write_text("config_version = 1\n")

    from ledgercore.errors import TomlConfigError
    with pytest.raises(TomlConfigError):
        load_project_context(tmp_path)


def test_wrong_registration_is_rejected(tmp_path: Path) -> None:
    """Project without Ledgercore bindings raises ARCHLEDGER_CONFIG_BINDING_INVALID."""
    from archledger.ledgercore_backend import ensure_archledger_registration
    project_uuid = str(uuid4())
    ensure_archledger_registration(
        tmp_path / ".ledger/ledger.toml",
        project_uuid=project_uuid,
        project_name="demo",
        data_storage="project",
    )
    # Write a tool config (no bindings created).
    config = build_default_project_config(tmp_path, archledger_dir="data", project_uuid=project_uuid)
    config_path = tmp_path / ".ledger/archledger/config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(render_project_config(config))

    with pytest.raises(ConfigError) as exc_info:
        load_project_context(tmp_path, require_initialized=False)

    assert exc_info.value.details.get("code") == "ARCHLEDGER_CONFIG_BINDING_INVALID"
