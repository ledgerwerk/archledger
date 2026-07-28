"""Sole adapter for detailed Ledgercore project/layout/binding/migration APIs.

All other Archledger modules must import Ledgercore through this module.
Generic stable utilities (atomic, frontmatter, hashing, ids, jsonio, jsonl,
refs, yamlio) may be imported directly from ledgercore.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import ledgercore
from ledgercore.errors import LedgerCoreError
from ledgercore.manifest import (
    EffectiveLedgerRegistration,
    LedgerProjectManifest,
    LedgerRegistration,
    LoadedLedgerProject,
    MountDefinition,
    StorageKind,
)
from ledgercore.storage_binding import (
    StorageValidationReport,
    read_storage_binding,
)

from archledger.errors import ConfigError

if TYPE_CHECKING:
    from ledgercore.layout import ResolvedLedgerLayout

# ---------------------------------------------------------------------------
# Archledger layout value object
# ---------------------------------------------------------------------------

DataStorage = Literal["project", "external", "user-data"]
DataSource = Literal["manifest", "local"]


@dataclass(frozen=True, slots=True)
class LedgercoreMigrationSupport:
    """Public migration capabilities exposed by the installed Ledgercore.

    Ledgercore versions can publish model types before their executor and
    recovery behavior is complete.  Capability detection therefore checks the
    public callable signatures as well as exported model types.  Consumers can
    use this value to report a truthful fallback instead of inferring support
    from the mere presence of a class.
    """

    version: str
    public_api: bool
    destination_policies: bool
    lifecycle_hooks: bool
    schema3_models: bool
    schema3_execution: bool
    recovery_analysis: bool
    resume: bool
    rollback: bool
    prepared_sources: bool

    @property
    def schema3_recovery(self) -> bool:
        """Whether the public API can analyze and act on schema-3 journals."""
        return self.recovery_analysis and (self.resume or self.rollback)


def ledgercore_version() -> str:
    """Return the installed Ledgercore version through its public package API."""
    return str(getattr(ledgercore, "__version__", "unknown"))


def ledgercore_migration_support() -> LedgercoreMigrationSupport:
    """Describe supported migration behavior without importing private modules."""
    plan_fn = getattr(ledgercore, "plan_storage_migration", None)
    validate_fn = getattr(ledgercore, "validate_storage_migration_plan", None)
    execute_fn = getattr(ledgercore, "execute_storage_migration", None)
    inspect_fn = getattr(ledgercore, "inspect_storage_migration", None)
    recover_fn = getattr(ledgercore, "recover_storage_migration", None)
    hooks_type = getattr(ledgercore, "StorageMigrationHooks", None)

    public_api = all(
        callable(function)
        for function in (plan_fn, validate_fn, execute_fn, inspect_fn, recover_fn)
    )
    execute_parameters = (
        inspect.signature(execute_fn).parameters if callable(execute_fn) else {}
    )
    recover_parameters = (
        inspect.signature(recover_fn).parameters if callable(recover_fn) else {}
    )
    lifecycle_hooks = "hooks" in execute_parameters
    recovery_analysis = any(
        name in recover_parameters for name in ("action", "dry_run", "analysis")
    )
    resume = "action" in recover_parameters
    rollback = resume
    schema3_models = all(
        hasattr(ledgercore, name)
        for name in (
            "Schema3MigrationJournal",
            "Schema3ItemJournalState",
            "Schema3ConfigSwitchState",
        )
    )
    prepared_sources = bool(
        hooks_type is not None
        and hasattr(hooks_type, "__dataclass_fields__")
        and "prepare_sources" in hooks_type.__dataclass_fields__
    )

    return LedgercoreMigrationSupport(
        version=ledgercore_version(),
        public_api=public_api,
        destination_policies=all(
            hasattr(ledgercore, name)
            for name in (
                "DestinationPolicy",
                "DestinationPrecondition",
                "inspect_storage_migration_destination",
            )
        ),
        lifecycle_hooks=lifecycle_hooks,
        schema3_models=schema3_models,
        schema3_execution=(
            public_api and lifecycle_hooks and schema3_models and prepared_sources
        ),
        recovery_analysis=recovery_analysis,
        resume=resume,
        rollback=rollback,
        prepared_sources=prepared_sources,
    )


def build_storage_migration_plan(*args: Any, **kwargs: Any) -> Any:
    """Build a Ledgercore storage plan through the public package facade."""
    return ledgercore.plan_storage_migration(*args, **kwargs)


def validate_storage_migration_plan(*args: Any, **kwargs: Any) -> Any:
    """Validate a Ledgercore storage plan through the public package facade."""
    return ledgercore.validate_storage_migration_plan(*args, **kwargs)


def execute_storage_migration(*args: Any, **kwargs: Any) -> Any:
    """Execute a validated storage plan through the public package facade."""
    return ledgercore.execute_storage_migration(*args, **kwargs)


def execute_archledger_storage_migration(
    plan: Any,
    *,
    project_root: Path,
    quiescence_check: Any = None,
    validate_staged: Any = None,
    validate_activated: Any = None,
    finalize: Any = None,
) -> Any:
    """Execute a storage plan with the installed public hook contract."""
    execute_fn = ledgercore.execute_storage_migration
    parameters = inspect.signature(execute_fn).parameters
    kwargs: dict[str, Any] = {"project_root": project_root}
    if "hooks" in parameters:
        hooks_type = getattr(ledgercore, "StorageMigrationHooks", None)
        if hooks_type is None:
            raise ConfigError(
                "Ledgercore advertises hooks but does not export the hook type"
            )
        kwargs["hooks"] = hooks_type(
            quiescence_check=quiescence_check,
            validate_staged=validate_staged,
            validate_activated=validate_activated,
            finalize=finalize,
            requires_staged_validation=validate_staged is not None,
            requires_activated_validation=validate_activated is not None,
            requires_finalization=finalize is not None,
        )
    elif "quiescence_check" in parameters:
        kwargs["quiescence_check"] = quiescence_check
    return execute_fn(plan, **kwargs)


def inspect_storage_migration(*args: Any, **kwargs: Any) -> Any:
    """Inspect a migration journal through the public package facade."""
    return ledgercore.inspect_storage_migration(*args, **kwargs)


def recover_storage_migration(*args: Any, **kwargs: Any) -> Any:
    """Recover a migration through the public package facade."""
    return ledgercore.recover_storage_migration(*args, **kwargs)


def migration_lock(*args: Any, **kwargs: Any) -> Any:
    """Construct Ledgercore's public migration lock."""
    return ledgercore.MigrationLock(*args, **kwargs)


def build_archledger_storage_migration_plan(
    root: Path,
    *,
    storage: DataStorage,
    external_root: str | None = None,
) -> Any:
    """Build a Ledgercore plan for changing Archledger's data mount.

    The target manifest is assembled from the loaded manifest, so unrelated
    ledger registrations remain part of the plan and are not silently lost.
    """
    if storage == "external" and not external_root:
        raise ConfigError("external storage requires an external root")
    loaded = ledgercore.load_ledger_project(root)
    current = loaded.manifest.ledgers.get("archledger")
    if current is None or "data" not in current.mounts:
        raise ConfigError("Archledger has no data mount to migrate")
    mount = MountDefinition(
        name="data",
        storage=storage,
        external_root=(
            _ledgercore_path(external_root) if storage == "external" else None
        ),
    )
    target_registration = LedgerRegistration(
        name="archledger",
        mounts={**current.mounts, "data": mount},
    )
    ledgers = dict(loaded.manifest.ledgers)
    ledgers["archledger"] = target_registration
    target_manifest = LedgerProjectManifest(
        schema_version=loaded.manifest.schema_version,
        project_uuid=loaded.manifest.project_uuid,
        project_name=loaded.manifest.project_name,
        ledgers=ledgers,
    )
    return ledgercore.plan_storage_migration(
        loaded,
        target_manifest,
        loaded.local_overrides,
        "archledger",
        mounts=("data",),
        include_config=False,
        cache_strategy="rebuild",
    )


def storage_migration_plan_to_mapping(plan: Any) -> dict[str, Any]:
    """Serialize a public Ledgercore storage plan without private imports."""
    from dataclasses import fields, is_dataclass

    def convert(value: Any) -> Any:
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, Mapping):
            return {str(key): convert(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [convert(item) for item in value]
        if is_dataclass(value):
            return {
                field.name: convert(getattr(value, field.name))
                for field in fields(value)
            }
        if hasattr(value, "value") and isinstance(value.value, str):
            return value.value
        return value

    result = convert(plan)
    if not isinstance(result, dict):
        raise ConfigError("Ledgercore returned an invalid storage migration plan")
    return result


@dataclass(frozen=True, slots=True)
class ArchledgerLedgerLayout:
    """Resolved project identity and paths from Ledgercore."""

    project_root: Path
    manifest_path: Path
    local_config_path: Path
    project_uuid: str
    project_name: str | None
    tool_config_path: Path
    data_root: Path
    data_storage: DataStorage
    data_source: DataSource
    external_root: Path | None
    config_binding_path: Path
    data_binding_path: Path
    storage_validation: StorageValidationReport

    # Ledgercore raw layout for compatibility consumers
    raw_layout: ResolvedLedgerLayout | None = None
    raw_effective: EffectiveLedgerRegistration | None = None


# ---------------------------------------------------------------------------
# Schema-3 loader
# ---------------------------------------------------------------------------


def load_archledger_layout(
    start: Path,
    *,
    require_registration: bool = True,
    environ: Mapping[str, str] | None = None,
) -> ArchledgerLedgerLayout:
    """Locate and resolve the schema-3 Archledger project layout.

    Args:
        start: Starting directory for project discovery (usually cwd).
        require_registration: If True, raise when no archledger registration exists.
        environ: Environment variables override (default: os.environ).
    """
    env = os.environ if environ is None else dict(environ)

    loaded = ledgercore.load_ledger_project(start)
    locator = loaded.locator
    manifest = loaded.manifest

    if "archledger" not in manifest.ledgers:
        if require_registration:
            raise _error(
                "The shared manifest has no Archledger registration. "
                "Run: archledger init",
                "ARCHLEDGER_REGISTRATION_MISSING",
            )
        return _make_unregistered_layout(locator, manifest, loaded)

    effective = loaded.effective_ledgers.get("archledger")
    if effective is None:
        if require_registration:
            raise _error(
                "The shared manifest has no Archledger registration "
                "after overrides. Run: archledger init",
                "ARCHLEDGER_REGISTRATION_MISSING",
            )
        return _make_unregistered_layout(locator, manifest, loaded)

    data_mount = effective.mounts.get("data")
    if data_mount is None:
        raise _error(
            "Archledger must define exactly one mount named data.",
            "ARCHLEDGER_REGISTRATION_CONFLICT",
        )

    tool_config_path = ledgercore.derive_tool_config_path(
        locator.project_root, "archledger"
    )
    data_root = _resolve_data_root(
        locator.project_root, data_mount, manifest.project_uuid, env
    )
    data_storage, data_source, external_root = _classify_data_mount(data_mount)

    config_binding_path = tool_config_path.parent / ".ledger-project.toml"
    data_binding_path = data_root / ".ledger-project.toml"

    try:
        layout = ledgercore.resolve_ledger_layout(
            locator,
            manifest,
            "archledger",
            local_overrides=loaded.local_overrides,
            environ=env,
        )
        storage_validation = ledgercore.validate_ledger_layout_storage(layout)
    except LedgerCoreError as exc:
        raise _error(
            f"Failed to resolve Archledger layout: {exc}",
            "ARCHLEDGER_MANIFEST_INVALID",
        ) from exc

    return ArchledgerLedgerLayout(
        project_root=locator.project_root.resolve(strict=False),
        manifest_path=locator.manifest_path.resolve(strict=False),
        local_config_path=locator.local_config_path.resolve(strict=False),
        project_uuid=manifest.project_uuid,
        project_name=manifest.project_name,
        tool_config_path=tool_config_path,
        data_root=data_root,
        data_storage=data_storage,
        data_source=data_source,
        external_root=external_root,
        config_binding_path=config_binding_path,
        data_binding_path=data_binding_path,
        storage_validation=storage_validation,
        raw_layout=layout,
        raw_effective=effective,
    )


def _make_unregistered_layout(
    locator: Any,
    manifest: Any,
    loaded: LoadedLedgerProject,
) -> ArchledgerLedgerLayout:
    """Build a minimal layout when archledger is not registered."""
    from ledgercore.storage_paths import derive_project_mount_path

    tool_config_path = ledgercore.derive_tool_config_path(
        locator.project_root, "archledger"
    )
    data_root = derive_project_mount_path(locator.project_root, "archledger", "data")
    return ArchledgerLedgerLayout(
        project_root=locator.project_root.resolve(strict=False),
        manifest_path=locator.manifest_path.resolve(strict=False),
        local_config_path=locator.local_config_path.resolve(strict=False),
        project_uuid=manifest.project_uuid,
        project_name=manifest.project_name,
        tool_config_path=tool_config_path,
        data_root=data_root,
        data_storage="project",
        data_source="manifest",
        external_root=None,
        config_binding_path=tool_config_path.parent / ".ledger-project.toml",
        data_binding_path=data_root / ".ledger-project.toml",
        storage_validation=StorageValidationReport(results=()),
    )


# ---------------------------------------------------------------------------
# Semantic validation
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ArchledgerStorageValidation:
    """Archledger-semantic validation result."""

    valid: bool
    config_binding_valid: bool
    data_binding_valid: bool
    mounts_valid: bool
    domain_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def validate_archledger_layout(
    layout: ArchledgerLedgerLayout,
    *,
    require_initialized: bool = False,
) -> ArchledgerStorageValidation:
    """Validate Archledger-specific semantics on top of Ledgercore resolution."""
    errors: list[str] = []
    warnings: list[str] = []

    effective = layout.raw_effective
    registered = effective is not None
    mounts_valid = registered
    if not registered:
        errors.append(
            "Archledger is not registered in the shared manifest; residual files "
            "are not a canonical layout."
        )
    if effective is not None:
        mount_names = set(effective.mounts)
        if mount_names != {"data"}:
            errors.append(
                f"Archledger must define exactly one mount named data; "
                f"got {sorted(mount_names)}"
            )

        data_mount = effective.mounts.get("data")
        if data_mount is not None:
            if data_mount.storage == "cache":
                errors.append("Archledger data mount must not use cache storage")
            if data_mount.storage not in ("project", "external", "user-data"):
                errors.append(
                    "Archledger data storage must be project, external, "
                    f"or user-data; got {data_mount.storage}"
                )

    config_valid = _check_binding(layout.config_binding_path, layout.project_uuid)
    if not config_valid:
        errors.append(
            f"Config binding at {layout.config_binding_path} is invalid or missing"
        )

    data_valid = _check_binding(layout.data_binding_path, layout.project_uuid)
    if not data_valid:
        errors.append(
            f"Data binding at {layout.data_binding_path} is invalid or missing"
        )

    if require_initialized:
        if not layout.tool_config_path.is_file():
            errors.append(f"Tool config not found: {layout.tool_config_path}")
        if not layout.data_root.is_dir():
            errors.append(f"Data root not found: {layout.data_root}")

    return ArchledgerStorageValidation(
        valid=len(errors) == 0,
        config_binding_valid=config_valid,
        data_binding_valid=data_valid,
        mounts_valid=mounts_valid,
        domain_valid=True,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Manifest mutation helpers
# ---------------------------------------------------------------------------


def ensure_archledger_registration(
    manifest_path: Path,
    *,
    project_uuid: str,
    project_name: str | None = None,
    data_storage: DataStorage = "project",
    external_root: str | None = None,
) -> None:
    """Ensure the shared manifest registers archledger with one data mount.

    Uses Ledgercore's manifest reader/writer to preserve unrelated tools.
    Creates the manifest when it does not yet exist.
    """
    from types import MappingProxyType

    from ledgercore.manifest import (
        LedgerRegistration,
        MountDefinition,
    )

    existing: Any = None
    if manifest_path.is_file():
        existing = ledgercore.read_ledger_manifest(manifest_path)
        schema = getattr(existing, "schema_version", None)
        if schema not in (2, 3):
            raise _error(
                f"Manifest at {manifest_path} is not schema 2 or 3.",
                "ARCHLEDGER_MANIFEST_INVALID",
            )

    # Build or extend the ledgers mapping.
    mount_def = MountDefinition(
        name="data",
        storage=data_storage,
        external_root=(
            _ledgercore_path(external_root) if data_storage == "external" else None
        ),
    )
    arch_registration = LedgerRegistration(
        name="archledger",
        mounts=MappingProxyType({"data": mount_def}),
    )

    if existing is not None:
        new_ledgers = dict(existing.ledgers)
        new_ledgers["archledger"] = arch_registration
        manifest = LedgerProjectManifest(
            schema_version=3,
            project_uuid=existing.project_uuid,
            project_name=existing.project_name or project_name,
            ledgers=MappingProxyType(new_ledgers),
        )
    else:
        manifest = LedgerProjectManifest(
            schema_version=3,
            project_uuid=project_uuid,
            project_name=project_name,
            ledgers=MappingProxyType({"archledger": arch_registration}),
        )

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    ledgercore.write_ledger_manifest(manifest_path, manifest, preserve_comments=True)


def set_archledger_data_override(
    local_config_path: Path,
    *,
    data_storage: DataStorage | None = None,
    external_root: str | None = None,
) -> None:
    """Set or update the local override for the Archledger data mount."""
    from ledgercore.overrides import set_local_mount_override

    manifest_path = local_config_path.parent / "ledger.toml"
    manifest = ledgercore.read_ledger_manifest(manifest_path)

    # Read existing local overrides or create empty.
    if local_config_path.is_file():
        local = ledgercore.read_ledger_local_config(local_config_path, base=manifest)
    else:
        from types import MappingProxyType

        from ledgercore.manifest import LedgerLocalOverrides

        local = LedgerLocalOverrides(schema_version=3, ledgers=MappingProxyType({}))

    updated = set_local_mount_override(
        manifest,
        local,
        "archledger",
        "data",
        storage=data_storage,
        root=_ledgercore_path(external_root) if external_root else None,
    )

    local_config_path.parent.mkdir(parents=True, exist_ok=True)
    ledgercore.write_ledger_local_config(
        local_config_path, updated, preserve_comments=True
    )


def clear_archledger_data_override(local_config_path: Path) -> None:
    """Remove the Archledger data mount override from the local config.

    If the local file becomes empty of ledgers, it is deleted.
    """
    from ledgercore.overrides import clear_local_mount_override

    if not local_config_path.is_file():
        return

    manifest_path = local_config_path.parent / "ledger.toml"
    manifest = ledgercore.read_ledger_manifest(manifest_path)

    local = ledgercore.read_ledger_local_config(local_config_path, base=manifest)
    updated = clear_local_mount_override(manifest, local, "archledger", "data")

    ledgercore.write_ledger_local_config(
        local_config_path, updated, preserve_comments=True, delete_if_empty=True
    )


# ---------------------------------------------------------------------------
# Binding initialization
# ---------------------------------------------------------------------------


def initialize_archledger_bindings(
    project_root: Path,
    project_uuid: str,
    project_name: str | None,
    data_storage: DataStorage,
    *,
    external_root: str | None = None,
) -> None:
    """Initialize config and data binding markers through Ledgercore."""
    loaded = ledgercore.load_ledger_project(project_root)
    layout = ledgercore.resolve_ledger_layout(
        loaded.locator,
        loaded.manifest,
        "archledger",
        local_overrides=loaded.local_overrides,
    )
    ledgercore.initialize_config_binding(layout)
    data_mount = layout.mounts.get("data")
    if data_mount is not None:
        ledgercore.initialize_storage_binding(data_mount, require_empty=False)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_data_root(
    project_root: Path,
    mount: Any,
    project_uuid: str,
    environ: Mapping[str, str],
) -> Path:
    storage = mount.storage
    if storage == "project":
        return ledgercore.derive_project_mount_path(project_root, "archledger", "data")
    elif storage == "external":
        if mount.external_root is None:
            raise _error(
                "External data mount requires root.",
                "ARCHLEDGER_EXTERNAL_ROOT_INVALID",
            )
        return ledgercore.derive_external_mount_path(
            mount.external_root,
            "archledger",
            project_uuid,
            "data",
            project_root=project_root,
        )
    elif storage == "user-data":
        from platformdirs import user_data_path

        user_root = user_data_path("ledgerwerk", appauthor=False)
        return ledgercore.derive_user_data_mount_path(
            user_root, "archledger", project_uuid, "data"
        )
    else:
        raise _error(
            f"Unsupported data storage: {storage}",
            "ARCHLEDGER_DATA_STORAGE_INVALID",
        )


def _ledgercore_path(value: Path | str) -> str:
    """Serialize a filesystem path using Ledgercore's portable path syntax.

    Ledgercore manifest and local-config roots deliberately use forward
    slashes, including for Windows drive paths.  ``str(Path)`` emits
    backslashes on Windows, so normalize at this adapter boundary before
    passing roots to Ledgercore.
    """
    return os.fspath(value).replace("\\", "/")


def _derive_data_root(
    project_root: Path,
    data_storage: DataStorage,
    project_uuid: str,
) -> Path:
    if data_storage == "project":
        return ledgercore.derive_project_mount_path(project_root, "archledger", "data")
    elif data_storage in ("external", "user-data"):
        from platformdirs import user_data_path

        user_root = user_data_path("ledgerwerk", appauthor=False)
        return ledgercore.derive_user_data_mount_path(
            user_root, "archledger", project_uuid, "data"
        )
    else:
        raise _error(
            f"Unsupported data storage: {data_storage}",
            "ARCHLEDGER_DATA_STORAGE_INVALID",
        )


def _classify_data_mount(
    mount: Any,
) -> tuple[DataStorage, DataSource, Path | None]:
    storage: DataStorage
    if mount.storage in ("project", "external", "user-data"):
        storage = mount.storage
    else:
        raise _error(
            f"Archledger data mount must not use {mount.storage} storage.",
            "ARCHLEDGER_DATA_STORAGE_INVALID",
        )

    source: DataSource = mount.source
    external_root: Path | None = None
    if storage == "external" and mount.external_root:
        external_root = Path(mount.external_root)

    return storage, source, external_root


def _check_binding(path: Path, project_uuid: str) -> bool:
    try:
        binding = ledgercore.read_storage_binding(path)
    except (OSError, LedgerCoreError):
        return False
    return binding.project_uuid == project_uuid and binding.tool == "archledger"


def _error(message: str, code: str) -> ConfigError:
    return ConfigError(message, details={"code": code})


# ---------------------------------------------------------------------------
# Thin wrappers for operations that other modules need.
# ---------------------------------------------------------------------------


def locate_ledger_project(
    start: Path, legacy_tool_filenames: tuple[str, ...] = ()
) -> Any:
    """Locate a Ledger project, including legacy detection.

    Wraps ledgercore.config.locate_ledger_project through the adapter.
    """
    from ledgercore.config import locate_ledger_project as _locate

    return _locate(start, legacy_tool_filenames=legacy_tool_filenames)


def parse_ledger_project_manifest(plain: Mapping[str, Any]) -> Any:
    """Parse a schema-2 manifest for migration purposes.

    Wraps ledgercore.layout.parse_ledger_project_manifest through the adapter.
    """
    from ledgercore.layout import parse_ledger_project_manifest as _parse

    return _parse(plain)


# ---------------------------------------------------------------------------
# Re-exports
# ---------------------------------------------------------------------------

__all__ = [
    "ArchledgerLedgerLayout",
    "ArchledgerStorageValidation",
    "DataStorage",
    "DataSource",
    "EffectiveLedgerRegistration",
    "LoadedLedgerProject",
    "StorageKind",
    "StorageValidationReport",
    "clear_archledger_data_override",
    "ensure_archledger_registration",
    "initialize_archledger_bindings",
    "load_archledger_layout",
    "locate_ledger_project",
    "parse_ledger_project_manifest",
    "set_archledger_data_override",
    "read_storage_binding",
    "validate_archledger_layout",
]
