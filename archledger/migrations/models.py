"""Domain models for Archledger migration lifecycle.

All models are immutable dataclasses without Typer dependencies.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class MigrationName(Enum):
    """Canonical migration names."""

    PROJECT_LAYOUT = "project-layout"
    IDENTITY_LEDGERCORE = "identity-ledgercore"
    METADATA_VERSIONED = "metadata-versioned"


class MigrationState(Enum):
    """Migration lifecycle states."""

    UNINITIALIZED = "uninitialized"
    LEGACY = "legacy"
    CANONICAL_READY = "canonical-ready"
    MIGRATION_REQUIRED = "migration-required"
    BLOCKED = "blocked"
    PARTIAL = "partial"
    RECOVERY_REQUIRED = "recovery-required"
    COMPLETED_WITH_LEGACY = "completed-with-legacy"
    CLEAN = "clean"


class IdentityPolicy(Enum):
    """Project identity adoption policies."""

    STRICT = "strict"
    ADOPT_PROJECT = "adopt-project"


@dataclass(frozen=True)
class MigrationCapabilities:
    """Honest capabilities of a migration handler."""

    plan: bool = True
    apply: bool = True
    recover: bool = True
    cleanup: bool = True
    requires_legacy_state: bool = True
    requires_project_layout: bool = False
    supports_resume: bool = False
    supports_rollback: bool = False
    supports_auto_recovery: bool = False

    @property
    def supports_plan(self) -> bool:
        return self.plan

    @property
    def supports_apply(self) -> bool:
        return self.apply

    @property
    def supports_recover(self) -> bool:
        return self.recover

    @property
    def supports_cleanup(self) -> bool:
        return self.cleanup


@dataclass(frozen=True)
class MigrationIssue:
    """An issue found during migration inspection."""

    severity: str  # "blocker", "warning", "info"
    code: str
    message: str
    remediation: tuple[str, ...] = ()


@dataclass(frozen=True)
class MigrationProjectInfo:
    """Project identity information for migration."""

    root: Path
    manifest_exists: bool
    manifest_uuid: str | None
    legacy_uuid: str | None
    target_uuid: str | None
    identity_policy: IdentityPolicy = IdentityPolicy.STRICT


@dataclass(frozen=True)
class MigrationSourceInfo:
    """Source information for migration."""

    config_path: Path | None
    data_root: Path | None
    config_version: int
    fingerprint: str
    file_count: int
    total_bytes: int


@dataclass(frozen=True)
class MigrationDestinationInfo:
    """Destination information for migration."""

    manifest_path: Path
    config_path: Path
    data_root: Path
    storage: str


@dataclass(frozen=True)
class MigrationInventory:
    """Inventory of records in the source."""

    records: int = 0
    sections: int = 0
    archived_records: int = 0
    tombstones: int = 0
    highest_number: int = 0
    stored_next_number: int = 0


@dataclass(frozen=True)
class MigrationOperation:
    """A single operation in a migration plan."""

    operation: str  # "copy", "rewrite", "write-config", "merge-manifest"
    source: str | None = None
    destination: str = ""
    sha256: str | None = None
    size: int | None = None
    reason: str | None = None
    config_version: int | None = None
    before_fingerprint: str | None = None
    target_fingerprint: str | None = None
    destination_policy: str | None = None
    hook: str | None = None


@dataclass(frozen=True)
class ArchledgerMigrationPlan:
    """Immutable migration plan."""

    schema: str = "archledger.migration-plan.v2"
    migration: str = ""
    tool: str = "archledger"
    migration_id: str = ""
    project: MigrationProjectInfo | None = None
    source: MigrationSourceInfo | None = None
    destination: MigrationDestinationInfo | None = None
    inventory: MigrationInventory | None = None
    operations: tuple[MigrationOperation, ...] = ()
    preconditions: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    ledgercore_plan: dict[str, Any] | None = None
    required_hooks: tuple[str, ...] = ()
    cleanup_policy: dict[str, Any] | None = None
    plan_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "schema": self.schema,
            "migration": self.migration,
            "tool": self.tool,
            "migration_id": self.migration_id or self._default_migration_id(),
        }
        if self.project:
            result["project"] = {
                "root": str(self.project.root),
                "manifest_exists": self.project.manifest_exists,
                "manifest_uuid": self.project.manifest_uuid,
                "legacy_uuid": self.project.legacy_uuid,
                "target_uuid": self.project.target_uuid,
                "identity_policy": self.project.identity_policy.value,
            }
        if self.source:
            result["source"] = {
                "config_path": str(self.source.config_path)
                if self.source.config_path
                else None,
                "data_root": str(self.source.data_root)
                if self.source.data_root
                else None,
                "config_version": self.source.config_version,
                "fingerprint": self.source.fingerprint,
                "file_count": self.source.file_count,
                "total_bytes": self.source.total_bytes,
            }
        if self.destination:
            result["destination"] = {
                "manifest_path": str(self.destination.manifest_path),
                "config_path": str(self.destination.config_path),
                "data_root": str(self.destination.data_root),
                "storage": self.destination.storage,
            }
        if self.inventory:
            result["inventory"] = {
                "records": self.inventory.records,
                "sections": self.inventory.sections,
                "archived_records": self.inventory.archived_records,
                "tombstones": self.inventory.tombstones,
                "highest_number": self.inventory.highest_number,
                "stored_next_number": self.inventory.stored_next_number,
            }
        result["operations"] = [
            {
                "operation": op.operation,
                "source": op.source,
                "destination": op.destination,
                "sha256": op.sha256,
                "size": op.size,
                "reason": op.reason,
                "config_version": op.config_version,
                "before_fingerprint": op.before_fingerprint,
                "target_fingerprint": op.target_fingerprint,
                "destination_policy": op.destination_policy,
                "hook": op.hook,
            }
            for op in self.operations
        ]
        result["preconditions"] = list(self.preconditions)
        result["blockers"] = list(self.blockers)
        result["warnings"] = list(self.warnings)
        result["ledgercore_plan"] = self.ledgercore_plan
        result["required_hooks"] = list(self.required_hooks)
        result["cleanup_policy"] = self.cleanup_policy
        result["plan_hash"] = self.plan_hash
        return result

    def _default_migration_id(self) -> str:
        """Derive a stable transaction identity without timestamps."""
        source = self.source.fingerprint if self.source else ""
        root = str(self.project.root.resolve(strict=False)) if self.project else ""
        token = f"{self.tool}\0{self.migration}\0{root}\0{source}"
        return "migration-" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class ArchledgerMigrationReceipt:
    """Receipt for a completed migration."""

    migration_id: str
    migration: str
    completed_at: str
    project_uuid_before: str | None
    project_uuid_after: str | None
    source_fingerprint: str
    canonical_fingerprint: str
    legacy_source_preserved: bool
    cleanup_available: bool
    cleanup_command: str
    copied_paths: tuple[str, ...] = ()
    rewritten_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "migration_id": self.migration_id,
            "migration": self.migration,
            "completed_at": self.completed_at,
            "project_uuid_before": self.project_uuid_before,
            "project_uuid_after": self.project_uuid_after,
            "source_fingerprint": self.source_fingerprint,
            "canonical_fingerprint": self.canonical_fingerprint,
            "legacy_source_preserved": self.legacy_source_preserved,
            "cleanup_available": self.cleanup_available,
            "cleanup_command": self.cleanup_command,
            "copied_paths": list(self.copied_paths),
            "rewritten_paths": list(self.rewritten_paths),
        }


@dataclass(frozen=True)
class MigrationStatusReport:
    """Status report for migration state."""

    state: MigrationState
    available_migrations: tuple[str, ...] = ()
    completed_migrations: tuple[str, ...] = ()
    pending_migrations: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    recommended_next: str | None = None
    journals: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "state": self.state.value,
            "available_migrations": list(self.available_migrations),
            "completed_migrations": list(self.completed_migrations),
            "pending_migrations": list(self.pending_migrations),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "recommended_next": self.recommended_next,
            "journals": list(self.journals),
        }
