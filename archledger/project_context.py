from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from archledger.config.model import ProjectConfig
from archledger.config.parse import load_project_config
from archledger.errors import ConfigError, StorageError
from archledger.ledgercore_backend import (
    DataStorage,
    StorageValidationReport,
    load_archledger_layout,
    validate_archledger_layout,
)
from archledger.storage.meta import read_storage_meta
from archledger.storage.paths import ProjectPaths

# Schema-3 paths — derived by Ledgercore.
MANIFEST_PATH = Path(".ledger/ledger.toml")
LOCAL_CONFIG_PATH = Path(".ledger/ledger.local.toml")
ARCHLEDGER_CONFIG_PATH = Path(".ledger/archledger/config.toml")
ARCHLEDGER_DATA_PATH = Path(".ledger/archledger/data")

ProjectStateKind = Literal["uninitialized", "legacy", "canonical", "partial", "invalid"]


@dataclass(frozen=True, slots=True)
class ArchledgerProjectContext:
    """Runtime authority for Archledger identity and resolved paths."""

    project_root: Path
    config_root: Path
    manifest_path: Path
    local_config_path: Path
    config_path: Path
    data_root: Path
    sections_dir: Path
    records_dir: Path
    archive_dir: Path
    migrations_dir: Path
    build_dir: Path
    storage_meta_path: Path
    source_state_path: Path
    document_state_path: Path
    project_uuid: str
    project_name: str | None
    data_storage: DataStorage = "project"
    data_source: str = "manifest"
    external_root: Path | None = None
    config: ProjectConfig | None = None
    layout: Any = None
    storage_validation: StorageValidationReport | None = None

    # Deprecated compatibility properties for one release.
    @property
    def workspace_root(self) -> Path:
        return self.project_root

    @property
    def archledger_dir(self) -> Path:
        return self.data_root

    @property
    def active_mount_name(self) -> str:
        return "data"

    @property
    def mount_storage(self) -> str:
        return self.data_storage

    @property
    def mount_scope(self) -> None:
        return None

    @property
    def mount_source(self) -> str:
        return self.data_source

    def project_paths(self) -> ProjectPaths:
        if self.config is None:
            raise ConfigError("Canonical Archledger configuration is not loaded.")
        return ProjectPaths(
            workspace_root=self.project_root,
            config_root=self.config_root,
            manifest_path=self.manifest_path,
            local_config_path=self.local_config_path,
            config_path=self.config_path,
            archledger_dir=self.data_root,
            sections_dir=self.sections_dir,
            records_dir=self.records_dir,
            archive_dir=self.archive_dir,
            build_dir=self.build_dir,
            storage_meta_path=self.storage_meta_path,
            source_state_path=self.source_state_path,
            document_state_path=self.document_state_path,
            mount_name="data",
            mount_storage=self.data_storage,
            mount_scope=None,
            mount_source=self.data_source,
        )


def _error(message: str, code: str) -> ConfigError:
    return ConfigError(message, details={"code": code})


def load_project_context(
    start: Path,
    *,
    require_initialized: bool = True,
    environ: Mapping[str, str] | None = None,
) -> ArchledgerProjectContext:
    """Load the schema-3 Archledger project context through Ledgercore.

    Raises ConfigError with stable codes when the project is missing,
    unregistered, misconfigured, or requires migration.
    """
    ledger_layout = load_archledger_layout(
        start,
        require_registration=True,
        environ=environ,
    )

    # Validate Archledger-specific semantics.
    arch_validation = validate_archledger_layout(
        ledger_layout,
        require_initialized=require_initialized,
    )
    if not arch_validation.valid:
        issues = "; ".join(arch_validation.errors)
        raise _error(
            f"Archledger storage validation failed: {issues}",
            "ARCHLEDGER_CONFIG_BINDING_INVALID",
        )

    # Load tool config.
    config_path = ledger_layout.tool_config_path
    try:
        config = load_project_config(config_path)
    except ConfigError as exc:
        raise _error(str(exc), "ARCHLEDGER_CONFIG_INVALID") from exc
    if config.config_version < 11:
        raise _error(
            "Archledger stable configuration must use config_version 11 or 12.",
            "ARCHLEDGER_CONFIG_INVALID",
        )

    data_root = ledger_layout.data_root
    project_root = ledger_layout.project_root

    # Derive domain paths below data_root.
    sections_dir = _inside(
        data_root,
        config.profiles.arc42.sections_dir,
        "profiles.arc42.sections_dir",
    )
    build_raw = config.build_output_dir
    build_dir = (
        project_root
        if build_raw == "."
        else _inside(project_root, build_raw, "build.default_output_dir")
    )
    _inside(build_dir, config.build_default_output, "build.default_output")
    _inside(build_dir, config.diagram_output_dir, "diagrams.output_dir")
    state_path = _inside(data_root, config.tracking_state_file, "tracking.state_file")

    if require_initialized:
        if not data_root.is_dir():
            raise _error(
                "Canonical Archledger data root is missing.",
                "ARCHLEDGER_DATA_ROOT_MISSING",
            )
        storage_path = data_root / "storage.yaml"
        try:
            meta = read_storage_meta(storage_path)
        except (OSError, StorageError) as exc:
            raise _error(
                f"Canonical Archledger storage is invalid: {exc}",
                "ARCHLEDGER_STORAGE_INVALID",
            ) from exc
        if meta.project_uuid != ledger_layout.project_uuid:
            raise _error(
                "storage.yaml project_uuid does not match the shared manifest.",
                "ARCHLEDGER_STORAGE_UUID_MISMATCH",
            )

    return ArchledgerProjectContext(
        project_root=project_root.resolve(),
        config_root=(project_root / ".ledger").resolve(),
        manifest_path=ledger_layout.manifest_path.resolve(),
        local_config_path=ledger_layout.local_config_path.resolve(),
        config_path=config_path.resolve(),
        data_root=data_root,
        sections_dir=sections_dir,
        records_dir=data_root / "records",
        archive_dir=data_root / "archive",
        migrations_dir=data_root / "migrations",
        build_dir=build_dir,
        storage_meta_path=data_root / "storage.yaml",
        source_state_path=state_path,
        document_state_path=data_root / "document-state.json",
        project_uuid=ledger_layout.project_uuid,
        project_name=ledger_layout.project_name,
        data_storage=ledger_layout.data_storage,
        data_source=ledger_layout.data_source,
        external_root=ledger_layout.external_root,
        config=config,
        layout=ledger_layout.raw_layout,
        storage_validation=ledger_layout.storage_validation,
    )


def classify_project_state(start: Path) -> ProjectStateKind:
    """Classify the project state for CLI presentation."""
    try:
        locator = _safe_locate(start)
    except Exception:
        return "invalid"

    if locator is None:
        return "uninitialized"
    if getattr(locator, "is_legacy", False):
        return "legacy"
    try:
        load_project_context(start)
    except ConfigError as exc:
        code = exc.details.get("code", "") if exc.details else ""
        if code in {
            "ARCHLEDGER_DATA_ROOT_MISSING",
            "ARCHLEDGER_CONFIG_MISSING",
            "ARCHLEDGER_STORAGE_INVALID",
        }:
            return "partial"
        return "invalid"
    return "canonical"


def _safe_locate(start: Path) -> Any | None:
    from archledger.ledgercore_backend import locate_ledger_project

    return locate_ledger_project(
        start, legacy_tool_filenames=("archledger.toml", ".archledger.toml")
    )


def _inside(base: Path, value: str, field_name: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else base / candidate).resolve(
        strict=False
    )
    try:
        resolved.relative_to(base.resolve(strict=False))
    except ValueError as exc:
        raise _error(
            f"{field_name} must stay inside {base}.",
            "ARCHLEDGER_CONFIG_INVALID",
        ) from exc
    return resolved


__all__ = [
    "ARCHLEDGER_CONFIG_PATH",
    "ARCHLEDGER_DATA_PATH",
    "ArchledgerProjectContext",
    "ProjectStateKind",
    "classify_project_state",
    "load_project_context",
]
