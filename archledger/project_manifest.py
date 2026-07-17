"""Thin semantic wrapper over Ledgercore manifest and local-config APIs.

Deprecated: new code should call ledgercore_backend directly.
This module exists for backward compatibility with existing callers.
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from archledger.config.model import normalize_project_name
from archledger.errors import ConfigError
from archledger.ledgercore_backend import (
    clear_archledger_data_override as _backend_clear_override,
)
from archledger.ledgercore_backend import (
    ensure_archledger_registration as _backend_ensure_registration,
)
from archledger.ledgercore_backend import (
    set_archledger_data_override as _backend_set_override,
)


def _error(message: str, code: str) -> ConfigError:
    return ConfigError(message, details={"code": code})


def _normalize_uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise _error(
            "Project UUID must be a valid UUID.",
            "ARCHLEDGER_MANIFEST_INVALID",
        ) from exc


def ensure_archledger_manifest(
    manifest_path: Path,
    *,
    project_uuid: str,
    project_name: str | None = None,
    data_storage: str = "project",
    external_root: str | None = None,
) -> None:
    """Ensure the shared manifest has a schema-3 Archledger registration."""
    _backend_ensure_registration(
        manifest_path,
        project_uuid=project_uuid,
        project_name=project_name,
        data_storage=data_storage,  # type: ignore[arg-type]
        external_root=external_root,
    )


def set_data_storage_override(
    local_config_path: Path,
    *,
    data_storage: str | None = None,
    external_root: str | None = None,
) -> None:
    """Set a local override for the Archledger data mount."""
    _backend_set_override(
        local_config_path,
        data_storage=data_storage,  # type: ignore[arg-type]
        external_root=external_root,
    )


def clear_data_storage_override(local_config_path: Path) -> None:
    """Remove the local data mount override."""
    _backend_clear_override(local_config_path)


__all__ = [
    "clear_data_storage_override",
    "ensure_archledger_manifest",
    "set_data_storage_override",
]


# ---------------------------------------------------------------------------
# Deprecated compatibility wrappers (migration-only)
# ---------------------------------------------------------------------------

import sys  # noqa: E402
from collections.abc import Mapping  # noqa: E402
from typing import Any, cast  # noqa: E402
from uuid import uuid4  # noqa: E402

from tomlkit import dumps, parse, table  # noqa: E402
from tomlkit.toml_document import TOMLDocument  # noqa: E402

from archledger.storage.common import write_text_atomic  # noqa: E402

if sys.version_info >= (3, 11):
    pass
else:
    pass


def load_manifest(path: Path) -> TOMLDocument:
    """Deprecated: use ledgercore_backend for manifest access."""
    try:
        return parse(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _error(
            f"Failed to parse shared manifest {path}: {exc}",
            "ARCHLEDGER_MANIFEST_INVALID",
        ) from exc


def manifest_text(document: TOMLDocument) -> str:
    """Deprecated."""
    return dumps(document)


def new_manifest(*, project_uuid: str, project_name: str) -> TOMLDocument:
    """Deprecated: creates schema-3 through the adapter instead."""
    document = TOMLDocument()
    document.add("schema_version", 3)
    project = table()
    project.add("uuid", _normalize_uuid(project_uuid))
    project.add("name", normalize_project_name(project_name))
    document.add("project", project)
    return ensure_archledger_registration(document)


def ensure_archledger_registration(document: TOMLDocument) -> TOMLDocument:
    """Deprecated: use ledgercore_backend.ensure_archledger_registration."""
    ledgers = document.get("ledgers")
    if not isinstance(ledgers, Mapping):
        if ledgers is not None:
            raise _error(
                "Manifest ledgers must be a table.",
                "ARCHLEDGER_MANIFEST_INVALID",
            )
        ledgers = table()
        document.add("ledgers", ledgers)
    ledgers = cast(Any, ledgers)
    registration = ledgers.get("archledger")
    if registration is not None and not isinstance(registration, Mapping):
        raise _error(
            "Archledger registration must be a table.",
            "ARCHLEDGER_REGISTRATION_CONFLICT",
        )
    if registration is None:
        registration = table()
        ledgers.add("archledger", registration)
    registration = cast(Any, registration)
    mounts = table()
    data = table()
    data.add("storage", "project")
    mounts.add("data", data)
    registration["mounts"] = mounts
    return document


def ensure_project_identity(
    document: TOMLDocument,
    *,
    project_uuid: str | None,
    project_name: str | None,
    default_name: str,
) -> tuple[str, str]:
    """Deprecated: use ledgercore_backend for identity management."""
    project = document.get("project")
    if not isinstance(project, Mapping):
        if project is not None:
            raise _error(
                "Manifest project must be a table.",
                "ARCHLEDGER_MANIFEST_INVALID",
            )
        project = table()
        document.add("project", project)
    project = cast(Any, project)
    stored_uuid = project.get("uuid")
    if stored_uuid is None:
        resolved_uuid = _normalize_uuid(project_uuid or str(uuid4()))
        project.add("uuid", resolved_uuid)
    else:
        resolved_uuid = _normalize_uuid(str(stored_uuid))
        if project_uuid is not None and _normalize_uuid(project_uuid) != resolved_uuid:
            raise _error(
                "Requested project UUID conflicts with .ledger/ledger.toml.",
                "ARCHLEDGER_STORAGE_UUID_MISMATCH",
            )
    stored_name = project.get("name")
    resolved_name = (
        normalize_project_name(str(stored_name))
        if stored_name
        else normalize_project_name(project_name or default_name)
    )
    if stored_name is None:
        project.add("name", resolved_name)
    elif (
        project_name is not None
        and normalize_project_name(project_name) != resolved_name
    ):
        raise _error(
            "Requested project name conflicts with .ledger/ledger.toml.",
            "ARCHLEDGER_MANIFEST_INVALID",
        )
    return resolved_uuid, resolved_name


def write_manifest(path: Path, document: TOMLDocument) -> None:
    """Deprecated: use ledgercore_backend for manifest writes."""
    write_text_atomic(path, dumps(document))
