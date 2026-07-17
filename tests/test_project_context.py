from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from archledger.config.render import build_default_project_config, render_project_config
from archledger.errors import ConfigError
from archledger.project_context import load_project_context


def _write_project(root: Path, *, registration: str = "") -> str:
    project_uuid = str(uuid4())
    (root / ".ledger/arch").mkdir(parents=True)
    default_registration = '''[ledgers.archledger.config]
location = "project"
path = "arch/config.toml"

[ledgers.archledger.mounts.data]
storage = "repository"
path = "arch/archledger"'''
    manifest = "\n".join(
        [
            "schema_version = 2",
            "",
            "[project]",
            f'uuid = "{project_uuid}"',
            'name = "demo"',
            "",
            registration or default_registration,
            "",
        ]
    )
    (root / ".ledger/ledger.toml").write_text(manifest)
    config = build_default_project_config(root, archledger_dir="arch/archledger")
    (root / ".ledger/arch/config.toml").write_text(render_project_config(config))
    return project_uuid


def test_context_resolves_exact_repository_mount(tmp_path: Path) -> None:
    project_uuid = _write_project(tmp_path)

    context = load_project_context(tmp_path, require_initialized=False)

    assert context.project_uuid == project_uuid
    assert context.config_path == tmp_path / ".ledger/arch/config.toml"
    assert context.data_root == tmp_path / ".ledger/arch/archledger"
    assert context.build_dir == tmp_path
    assert context.active_mount_name == "data"
    assert context.mount_storage == "repository"


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

    assert context.data_root == tmp_path / ".ledger/arch/archledger"


def test_legacy_locator_requires_explicit_migration(tmp_path: Path) -> None:
    (tmp_path / ".archledger.toml").write_text("config_version = 1\n")

    with pytest.raises(ConfigError) as exc_info:
        load_project_context(tmp_path)

    assert exc_info.value.details["code"] == "ARCHLEDGER_MIGRATION_REQUIRED"


def test_wrong_registration_is_rejected(tmp_path: Path) -> None:
    _write_project(
        tmp_path,
        registration='''[ledgers.archledger.config]
location = "project"
path = "wrong/config.toml"

[ledgers.archledger.mounts.data]
storage = "repository"
path = "wrong/data"''',
    )

    with pytest.raises(ConfigError) as exc_info:
        load_project_context(tmp_path, require_initialized=False)

    assert exc_info.value.details["code"] == "ARCHLEDGER_REGISTRATION_CONFLICT"
