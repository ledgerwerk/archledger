from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

from tomlkit import dumps, parse, table
from tomlkit.toml_document import TOMLDocument

from archledger.config.model import normalize_project_name
from archledger.errors import ConfigError
from archledger.storage.common import write_text_atomic


def _error(message: str, code: str) -> ConfigError:
    return ConfigError(message, details={"code": code})


def _normalize_uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise _error(
            "Project UUID must be a valid UUID.", "ARCHLEDGER_MANIFEST_INVALID"
        ) from exc


def new_manifest(*, project_uuid: str, project_name: str) -> TOMLDocument:
    document = TOMLDocument()
    document.add("schema_version", 2)
    project = table()
    project.add("uuid", _normalize_uuid(project_uuid))
    project.add("name", normalize_project_name(project_name))
    document.add("project", project)
    workspace = table()
    workspace.add("default_provider", "user-data")
    workspace.add("namespace", "ledgerwerk")
    cache = table()
    cache.add("default_provider", "user-cache")
    cache.add("namespace", "ledgerwerk")
    storage = table()
    storage.add("workspace", workspace)
    storage.add("cache", cache)
    document.add("storage", storage)
    return ensure_archledger_registration(document)


def load_manifest(path: Path) -> TOMLDocument:
    try:
        return parse(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _error(
            f"Failed to parse shared manifest {path}: {exc}",
            "ARCHLEDGER_MANIFEST_INVALID",
        ) from exc


def ensure_project_identity(
    document: TOMLDocument,
    *,
    project_uuid: str | None,
    project_name: str | None,
    default_name: str,
) -> tuple[str, str]:
    project = document.get("project")
    if not isinstance(project, Mapping):
        if project is not None:
            raise _error(
                "Manifest project must be a table.", "ARCHLEDGER_MANIFEST_INVALID"
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


def ensure_archledger_registration(document: TOMLDocument) -> TOMLDocument:
    ledgers = document.get("ledgers")
    if not isinstance(ledgers, Mapping):
        if ledgers is not None:
            raise _error(
                "Manifest ledgers must be a table.", "ARCHLEDGER_MANIFEST_INVALID"
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
    config = table()
    config.add("location", "project")
    config.add("path", "arch/config.toml")
    data = table()
    data.add("storage", "repository")
    data.add("path", "arch/archledger")
    mounts = table()
    mounts.add("data", data)
    registration["config"] = config
    registration["mounts"] = mounts
    return document


def write_manifest(path: Path, document: TOMLDocument) -> None:
    write_text_atomic(path, dumps(document))


def manifest_text(document: TOMLDocument) -> str:
    return dumps(document)
