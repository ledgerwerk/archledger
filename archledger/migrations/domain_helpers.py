"""Shared deterministic helpers for Archledger-owned domain migrations."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from archledger.config.model import ProjectConfig
from archledger.migrations.models import (
    ArchledgerMigrationPlan,
    MigrationDestinationInfo,
    MigrationInventory,
    MigrationOperation,
    MigrationProjectInfo,
    MigrationSourceInfo,
)
from archledger.storage.frontmatter import iter_source_files
from archledger.storage.paths import ProjectPaths


def source_fingerprint(paths: ProjectPaths, config: ProjectConfig) -> str:
    """Fingerprint all domain inputs that a rewrite service can mutate."""
    hasher = hashlib.sha256()
    roots = (paths.sections_dir, paths.records_dir, paths.archive_dir)
    for root in roots:
        for path in sorted(
            iter_source_files(root, (config.section_extension, config.record_extension))
        ):
            relative = path.relative_to(paths.workspace_root).as_posix()
            hasher.update(relative.encode("utf-8"))
            hasher.update(path.read_bytes())
    for path in (paths.config_path, paths.storage_meta_path, paths.source_state_path):
        if path.is_file():
            hasher.update(
                path.relative_to(paths.workspace_root).as_posix().encode("utf-8")
            )
            hasher.update(path.read_bytes())
    return "sha256:" + hasher.hexdigest()


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def plan_for_domain(
    *,
    migration: str,
    paths: ProjectPaths,
    config: ProjectConfig,
    operations: tuple[MigrationOperation, ...],
    inventory: MigrationInventory | None = None,
) -> ArchledgerMigrationPlan:
    fingerprint = source_fingerprint(paths, config)
    project = MigrationProjectInfo(
        root=paths.workspace_root.resolve(strict=False),
        manifest_exists=paths.manifest_path.is_file(),
        manifest_uuid=config.project_uuid,
        legacy_uuid=config.project_uuid,
        target_uuid=config.project_uuid,
    )
    source = MigrationSourceInfo(
        config_path=paths.config_path.resolve(strict=False),
        data_root=paths.archledger_dir.resolve(strict=False),
        config_version=config.config_version,
        fingerprint=fingerprint,
        file_count=len(
            [
                path
                for root in (paths.sections_dir, paths.records_dir, paths.archive_dir)
                for path in iter_source_files(
                    root, (config.section_extension, config.record_extension)
                )
            ]
        ),
        total_bytes=0,
    )
    destination = MigrationDestinationInfo(
        manifest_path=paths.manifest_path.resolve(strict=False),
        config_path=paths.config_path.resolve(strict=False),
        data_root=paths.archledger_dir.resolve(strict=False),
        storage=paths.mount_storage,
    )
    plan = ArchledgerMigrationPlan(
        migration=migration,
        project=project,
        source=source,
        destination=destination,
        inventory=inventory,
        operations=operations,
        preconditions=(
            "source fingerprint matches",
            "project root matches",
            "migration lock is available",
        ),
        required_hooks=("quiescence_check",),
        cleanup_policy={"source_deletion": False},
    )
    from archledger.migrations.plan_io import compute_plan_hash

    return ArchledgerMigrationPlan(
        schema=plan.schema,
        migration=plan.migration,
        tool=plan.tool,
        migration_id=plan.to_dict()["migration_id"],
        project=plan.project,
        source=plan.source,
        destination=plan.destination,
        inventory=plan.inventory,
        operations=plan.operations,
        preconditions=plan.preconditions,
        blockers=plan.blockers,
        warnings=plan.warnings,
        required_hooks=plan.required_hooks,
        cleanup_policy=plan.cleanup_policy,
        plan_hash=compute_plan_hash(plan.to_dict()),
    )


def validate_domain_plan(
    plan: ArchledgerMigrationPlan,
    paths: ProjectPaths,
    config: ProjectConfig,
) -> None:
    """Reject a plan before the domain service performs any write."""
    from archledger.migrations.plan_io import check_plan_staleness

    if plan.migration_id == "":
        raise ValueError("migration plan has no migration_id")
    issues = check_plan_staleness(
        plan, source_fingerprint(paths, config), paths.workspace_root
    )
    if issues:
        from archledger.errors import StorageError

        raise StorageError(
            "Migration plan is stale: " + "; ".join(issues),
            details={
                "code": "stale_plan",
                "remediation": ["Recreate the migration plan."],
            },
        )


def relative_operations(
    paths: ProjectPaths, operation: Callable[[Path], MigrationOperation]
) -> tuple[MigrationOperation, ...]:
    """Build deterministic operations over all canonical source files."""
    files = sorted(
        path
        for root in (paths.sections_dir, paths.records_dir, paths.archive_dir)
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    )
    return tuple(operation(path) for path in files)


def storage_layout_fingerprint(layout: Any) -> str:
    """Fingerprint the topology inputs used by a storage-layout plan."""
    hasher = hashlib.sha256()
    for path in (
        layout.manifest_path,
        layout.local_config_path,
        layout.config_binding_path,
        layout.data_binding_path,
    ):
        if path.is_file():
            hasher.update(str(path.resolve(strict=False)).encode("utf-8"))
            hasher.update(path.read_bytes())
    if layout.data_root.is_dir():
        for path in sorted(
            path for path in layout.data_root.rglob("*") if path.is_file()
        ):
            hasher.update(str(path.relative_to(layout.data_root)).encode("utf-8"))
            hasher.update(path.read_bytes())
    return "sha256:" + hasher.hexdigest()


def plan_for_storage_layout(
    *,
    root: Path,
    layout: Any,
    target_storage: str,
    external_root: str | None,
    ledgercore_plan: dict[str, Any],
) -> ArchledgerMigrationPlan:
    """Wrap a public Ledgercore storage plan in Archledger's strict envelope."""
    fingerprint = storage_layout_fingerprint(layout)
    project = MigrationProjectInfo(
        root=root.resolve(strict=False),
        manifest_exists=layout.manifest_path.is_file(),
        manifest_uuid=layout.project_uuid,
        legacy_uuid=None,
        target_uuid=layout.project_uuid,
    )
    source = MigrationSourceInfo(
        config_path=layout.manifest_path.resolve(strict=False),
        data_root=layout.data_root.resolve(strict=False),
        config_version=3,
        fingerprint=fingerprint,
        file_count=sum(1 for path in layout.data_root.rglob("*") if path.is_file())
        if layout.data_root.is_dir()
        else 0,
        total_bytes=0,
    )
    items = ledgercore_plan.get("items", [])
    operations = tuple(
        MigrationOperation(
            operation="storage-migrate",
            source="data",
            destination="data",
            reason=f"change Archledger data storage to {target_storage}",
            destination_policy=(
                item.get("destination_policy") if isinstance(item, dict) else None
            ),
        )
        for item in items[:1]
    ) or (
        MigrationOperation(
            operation="storage-migrate",
            source="data",
            destination="data",
            reason=f"change Archledger data storage to {target_storage}",
        ),
    )
    plan = ArchledgerMigrationPlan(
        migration="storage-layout",
        project=project,
        source=source,
        destination=MigrationDestinationInfo(
            manifest_path=layout.manifest_path.resolve(strict=False),
            config_path=layout.tool_config_path.resolve(strict=False),
            data_root=(
                Path(items[0]["destination"]).resolve(strict=False)
                if items and isinstance(items[0], dict) and items[0].get("destination")
                else layout.data_root.resolve(strict=False)
            ),
            storage=target_storage,
        ),
        operations=operations,
        preconditions=(
            "source topology fingerprint matches",
            "project identity matches",
            "migration lock is available",
            "destination policy is satisfied",
        ),
        ledgercore_plan={
            "target_storage": target_storage,
            "external_root": external_root,
            "plan": ledgercore_plan,
        },
        required_hooks=("quiescence_check",),
        cleanup_policy={"source_deletion": False, "requires_receipt": True},
    )
    from archledger.migrations.plan_io import compute_plan_hash

    return ArchledgerMigrationPlan(
        schema=plan.schema,
        migration=plan.migration,
        tool=plan.tool,
        migration_id=plan.to_dict()["migration_id"],
        project=plan.project,
        source=plan.source,
        destination=plan.destination,
        operations=plan.operations,
        preconditions=plan.preconditions,
        blockers=plan.blockers,
        warnings=plan.warnings,
        ledgercore_plan=plan.ledgercore_plan,
        required_hooks=plan.required_hooks,
        cleanup_policy=plan.cleanup_policy,
        plan_hash=compute_plan_hash(plan.to_dict()),
    )
