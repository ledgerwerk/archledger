from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ledgercore.paths import is_relative_to as core_is_relative_to

from archledger.errors import ConfigError
from archledger.storage.project_config import ProjectConfig

CANONICAL_PROJECT_CONFIG_FILENAME = "ledger.toml"
HIDDEN_PROJECT_CONFIG_FILENAME = "ledger.local.toml"
PROJECT_CONFIG_FILENAMES = (CANONICAL_PROJECT_CONFIG_FILENAME,)
DEFAULT_ARCHLEDGER_DIR_NAME = ".ledger/arch/archledger"


def is_relative_to(path: Path, parent: Path) -> bool:
    return core_is_relative_to(path, parent)


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    workspace_root: Path
    config_root: Path
    manifest_path: Path
    local_config_path: Path
    config_path: Path
    archledger_dir: Path
    sections_dir: Path
    records_dir: Path
    archive_dir: Path
    build_dir: Path
    storage_meta_path: Path
    source_state_path: Path
    document_state_path: Path
    mount_name: str = "data"
    mount_storage: str = "repository"
    mount_scope: str | None = None
    mount_source: str = "repository"


def discover_project_config(start: Path) -> tuple[Path, list[str]]:
    """Discover the canonical shared manifest for compatibility callers."""
    from ledgercore.config import locate_ledger_project

    locator = locate_ledger_project(
        start,
        legacy_tool_filenames=("archledger.toml", ".archledger.toml"),
    )
    if locator is None:
        raise ConfigError(
            "No .ledger/ledger.toml found. Run: archledger init",
            details={"code": "ARCHLEDGER_PROJECT_NOT_FOUND"},
        )
    if locator.is_legacy:
        raise ConfigError(
            "Legacy Archledger layout found. Run: archledger migrate project",
            details={"code": "ARCHLEDGER_MIGRATION_REQUIRED"},
        )
    return locator.manifest_path, []


def resolve_project_paths(start: Path) -> tuple[ProjectPaths, ProjectConfig, list[str]]:
    """Resolve paths through Ledgercore's canonical project context."""
    from archledger.project_context import load_project_context

    context = load_project_context(start)
    if not isinstance(context.config, ProjectConfig):
        raise ConfigError("Canonical Archledger configuration is invalid.")
    return context.project_paths(), context.config, []


# Kept for callers that use the path-confinement helper directly.
def _resolve_relative_child(
    base_dir: Path,
    relative_path: str,
    field_name: str,
    *,
    parent_label: str,
) -> Path:
    candidate = Path(relative_path)
    resolved = (candidate if candidate.is_absolute() else base_dir / candidate).resolve(
        strict=False
    )
    try:
        resolved.relative_to(base_dir.resolve(strict=False))
    except ValueError as exc:
        raise ConfigError(f"{field_name} must stay inside {parent_label}.") from exc
    return resolved
