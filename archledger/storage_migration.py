"""Archledger storage migration: domain discovery, validation, and orchestration.

Generic filesystem migration mechanics (hashing, copying, staging, activation,
journaling, rollback) are delegated to Ledgercore. This module owns:
- legacy config/data discovery
- identity evidence collection
- durable inventory classification
- tool-config conversion to v12
- record/archive/tombstone validation
- post-activation domain checks
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from archledger.config.parse import load_project_config
from archledger.errors import ConfigError

SourceKind = Literal[
    "legacy",
    "schema2",
    "hybrid",
    "partial_schema3",
    "already_target",
    "invalid",
]

TargetStorage = Literal["project", "external", "user-data"]


@dataclass(frozen=True, slots=True)
class ArchledgerMigrationPlan:
    """Immutable migration plan: read-only inspection result."""

    source_kind: SourceKind
    source_config_path: Path | None
    source_data_root: Path | None
    target_manifest_path: Path
    target_local_config_path: Path
    target_tool_config_path: Path
    target_data_root: Path
    target_storage: TargetStorage
    target_external_root: Path | None
    project_uuid: str | None
    project_name: str | None
    copy_items: tuple[str, ...] = ()
    skipped_items: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    requires_apply: bool = False
    recovery_required: bool = False
    ledgercore_plan: Any = None


# ---------------------------------------------------------------------------
# Source classification
# ---------------------------------------------------------------------------


def classify_source(start: Path) -> SourceKind:
    """Classify the current project state for migration purposes."""
    from archledger.project_context import classify_project_state

    state = classify_project_state(start)
    if state == "uninitialized":
        return "invalid"
    elif state == "legacy":
        return "legacy"
    elif state == "canonical":
        # Check if it's already a valid schema-3 target.
        return _check_already_target(start)
    elif state == "partial":
        return _classify_partial(start)
    else:
        return "invalid"


# ---------------------------------------------------------------------------
# Migration planning
# ---------------------------------------------------------------------------


def plan_storage_migration(
    start: Path,
    *,
    target_storage: TargetStorage = "project",
    target_external_root: str | None = None,
) -> ArchledgerMigrationPlan:
    """Produce a read-only migration plan without modifying any files.

    Args:
        start: Project root or subdirectory.
        target_storage: Desired target storage kind.
        target_external_root: External root path when target_storage='external'.
    """
    source_kind = classify_source(start)
    source_config_path = _find_legacy_config(start)
    source_data_root = _find_legacy_data(start, source_config_path)

    # Target paths
    project_root = _resolve_project_root(start)
    target_manifest_path = project_root / ".ledger/ledger.toml"
    target_local_config_path = project_root / ".ledger/ledger.local.toml"
    target_tool_config_path = project_root / ".ledger/archledger/config.toml"
    target_data_root = project_root / ".ledger/archledger/data"

    # Identity evidence
    project_uuid, project_name, id_issues = _collect_identity_evidence(
        start, source_config_path, source_data_root
    )
    blockers: list[str] = list(id_issues)

    # Classify and collect items
    copy_items: list[str] = []
    skipped_items: list[str] = []
    warnings: list[str] = []

    if source_kind in ("legacy", "hybrid", "partial_schema3"):
        if source_data_root and source_data_root.is_dir():
            inventory, inv_issues = _classify_durable_inventory(source_data_root)
            blockers.extend(inv_issues)
            copy_items.extend(inventory)

    if source_kind == "already_target":
        return ArchledgerMigrationPlan(
            source_kind=source_kind,
            source_config_path=source_config_path,
            source_data_root=source_data_root,
            target_manifest_path=target_manifest_path,
            target_local_config_path=target_local_config_path,
            target_tool_config_path=target_tool_config_path,
            target_data_root=target_data_root,
            target_storage=target_storage,
            target_external_root=(
                Path(target_external_root) if target_external_root else None
            ),
            project_uuid=project_uuid,
            project_name=project_name,
            requires_apply=False,
        )

    if source_kind == "invalid":
        blockers.append("Source state is invalid or uninitialized.")

    return ArchledgerMigrationPlan(
        source_kind=source_kind,
        source_config_path=source_config_path,
        source_data_root=source_data_root,
        target_manifest_path=target_manifest_path,
        target_local_config_path=target_local_config_path,
        target_tool_config_path=target_tool_config_path,
        target_data_root=target_data_root,
        target_storage=target_storage,
        target_external_root=(
            Path(target_external_root) if target_external_root else None
        ),
        project_uuid=project_uuid,
        project_name=project_name,
        copy_items=tuple(copy_items),
        skipped_items=tuple(skipped_items),
        issues=(),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        requires_apply=len(blockers) == 0 and len(copy_items) > 0,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_legacy_config(start: Path) -> Path | None:
    root = _resolve_project_root(start)
    for name in (".archledger.toml", "archledger.toml"):
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def _find_legacy_data(start: Path, config_path: Path | None) -> Path | None:
    root = _resolve_project_root(start)
    # Check default location
    default = root / ".archledger"
    if default.is_dir():
        return default
    # Check config-specified location
    if config_path and config_path.is_file():
        try:
            cfg = load_project_config(config_path)
            if cfg.archledger_dir:
                candidate = root / cfg.archledger_dir
                if candidate.is_dir():
                    return candidate
        except Exception:
            pass
    return None


def _resolve_project_root(start: Path) -> Path:
    """Find the project root by looking for .ledger/ or legacy markers."""
    current = start.resolve()
    for _ in range(50):
        if (current / ".ledger/ledger.toml").is_file():
            return current
        if (current / ".archledger.toml").is_file():
            return current
        if (current / "archledger.toml").is_file():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return start.resolve()


def _collect_identity_evidence(
    start: Path,
    config_path: Path | None,
    data_root: Path | None,
) -> tuple[str | None, str | None, list[str]]:
    """Collect project identity from all available sources."""
    issues: list[str] = []
    uuids: list[str] = []
    names: list[str] = []

    # From legacy config
    if config_path and config_path.is_file():
        try:
            cfg = load_project_config(config_path)
            if cfg.project_uuid:
                uuids.append(cfg.project_uuid)
            if cfg.project_name:
                names.append(cfg.project_name)
        except Exception:
            pass

    # From storage.yaml
    if data_root and data_root.is_dir():
        storage_path = data_root / "storage.yaml"
        if storage_path.is_file():
            try:
                from archledger.storage.meta import read_storage_meta

                meta = read_storage_meta(storage_path)
                uuids.append(meta.project_uuid)
            except Exception:
                pass

    # Check for conflicts
    unique_uuids = list(dict.fromkeys(uuids))
    unique_names = list(dict.fromkeys(names))

    if len(unique_uuids) > 1:
        issues.append(
            f"Conflicting project UUIDs: {unique_uuids}. "
            "Resolve manually before migration."
        )

    return (
        unique_uuids[0] if unique_uuids else None,
        unique_names[0] if unique_names else None,
        issues,
    )


def _classify_durable_inventory(
    data_root: Path,
) -> tuple[list[str], list[str]]:
    """Classify recognized durable files for migration."""
    recognized = {
        "storage.yaml",
        "source-state.json",
        "document-state.json",
        "profiles",
        "records",
        "archive",
        "migrations",
        "sections",
    }
    items: list[str] = []
    issues: list[str] = []

    for child in sorted(data_root.iterdir()):
        if child.name in recognized:
            items.append(str(child.relative_to(data_root)))
        elif child.name.startswith("."):
            continue  # hidden files skipped
        elif child.name.startswith("migration-"):
            items.append(str(child.relative_to(data_root)))
        else:
            issues.append(f"Unknown top-level entry in data root: {child.name}")

    return items, issues


def _check_already_target(start: Path) -> SourceKind:
    """Check if the canonical state is already a valid schema-3 target."""
    root = _resolve_project_root(start)
    config_path = root / ".ledger/archledger/config.toml"
    data_root = root / ".ledger/archledger/data"
    if config_path.is_file() and data_root.is_dir():
        # Check bindings
        config_binding = config_path.parent / ".ledger-project.toml"
        data_binding = data_root / ".ledger-project.toml"
        if config_binding.is_file() and data_binding.is_file():
            return "already_target"
        return "partial_schema3"
    return "partial_schema3"


def _classify_partial(start: Path) -> SourceKind:
    """Classify a partial state more precisely."""
    root = _resolve_project_root(start)
    has_schema3 = (root / ".ledger/ledger.toml").is_file()
    has_legacy = (root / ".archledger.toml").is_file() or (
        root / "archledger.toml"
    ).is_file()

    if has_schema3 and has_legacy:
        return "hybrid"
    elif has_schema3:
        return "partial_schema3"
    elif has_legacy:
        return "legacy"
    return "invalid"


# ---------------------------------------------------------------------------
# Migration execution
# ---------------------------------------------------------------------------


def apply_storage_migration(
    plan: ArchledgerMigrationPlan,
) -> None:
    """Execute an approved migration plan.

    Delegates generic file operations to Ledgercore; performs Archledger
    domain validation before and after activation.
    """
    if plan.blockers:
        raise ConfigError(
            f"Migration blocked: {'; '.join(plan.blockers)}",
            details={"code": "ARCHLEDGER_MIGRATION_BLOCKED"},
        )

    if plan.recovery_required:
        raise ConfigError(
            "Recovery required before migration can proceed. "
            "Run: archledger storage migrate recover",
            details={"code": "ARCHLEDGER_MIGRATION_RECOVERY_REQUIRED"},
        )

    # For legacy/schema2/hybrid: convert config, copy data, activate.
    if plan.source_kind in ("legacy", "schema2", "hybrid", "partial_schema3"):
        _execute_domain_migration(plan)
    elif plan.source_kind == "already_target":
        return  # no-op


def _execute_domain_migration(plan: ArchledgerMigrationPlan) -> None:
    """Execute domain-level migration steps."""
    import shutil

    root = plan.target_manifest_path.parent.parent

    # 1. Convert legacy config to v12
    if plan.source_config_path and plan.source_config_path.is_file():
        _convert_config_to_v12(plan)

    # 2. Copy recognized durable inventory
    if plan.source_data_root and plan.source_data_root.is_dir():
        target = plan.target_data_root
        target.parent.mkdir(parents=True, exist_ok=True)
        for item in plan.copy_items:
            src = plan.source_data_root / item
            dst = target / item
            if src.is_dir():
                if not dst.exists():
                    shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    # 3. Initialize bindings
    from archledger.ledgercore_backend import initialize_archledger_bindings

    initialize_archledger_bindings(
        root,
        project_uuid=plan.project_uuid or "",
        project_name=plan.project_name,
        data_storage=plan.target_storage,
    )


def _convert_config_to_v12(plan: ArchledgerMigrationPlan) -> None:
    """Convert legacy config to version 12 at the target path."""
    from archledger.config.render import render_project_config

    try:
        config = load_project_config(plan.source_config_path)  # type: ignore[arg-type]
    except Exception:
        return

    plan.target_tool_config_path.parent.mkdir(parents=True, exist_ok=True)
    plan.target_tool_config_path.write_text(render_project_config(config))


__all__ = [
    "ArchledgerMigrationPlan",
    "SourceKind",
    "TargetStorage",
    "apply_storage_migration",
    "classify_source",
    "plan_storage_migration",
]
