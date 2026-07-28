"""Ledgercore-backed storage topology migration handler."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from archledger.errors import StorageError
from archledger.ledgercore_backend import (
    build_archledger_storage_migration_plan,
    execute_archledger_storage_migration,
    inspect_storage_migration,
    ledgercore_migration_support,
    load_archledger_layout,
    recover_storage_migration,
    storage_migration_plan_to_mapping,
    validate_storage_migration_plan,
)
from archledger.migrations.domain_helpers import (
    plan_for_storage_layout,
    storage_layout_fingerprint,
)
from archledger.migrations.models import ArchledgerMigrationPlan, MigrationCapabilities
from archledger.migrations.plan_io import check_plan_staleness
from archledger.migrations.receipts import create_receipt, write_receipt


class StorageLayoutHandler:
    """Plan and, when Ledgercore supports it, execute a topology change."""

    name = "storage-layout"
    summary = "Migrate Archledger data between project, external, and user storage"

    @property
    def capabilities(self) -> MigrationCapabilities:
        support = ledgercore_migration_support()
        return MigrationCapabilities(
            plan=True,
            apply=support.schema3_execution,
            recover=support.schema3_recovery,
            cleanup=False,
            requires_legacy_state=False,
            requires_project_layout=True,
            supports_resume=support.resume,
            supports_rollback=support.rollback,
            supports_auto_recovery=support.schema3_recovery,
        )

    def status(self, root: Path) -> dict[str, Any]:
        support = ledgercore_migration_support()
        try:
            layout = load_archledger_layout(root, require_registration=True)
        except Exception as exc:
            return {
                "state": "requires-project-layout",
                "ledgercore_version": support.version,
                "capabilities": self._capability_payload(support),
                "error": str(exc),
            }
        return {
            "state": "available",
            "current_storage": layout.data_storage,
            "current_data_root": str(layout.data_root),
            "ledgercore_version": support.version,
            "capabilities": self._capability_payload(support),
        }

    def plan(self, root: Path, options: dict[str, Any]) -> ArchledgerMigrationPlan:
        storage = str(options.get("storage", options.get("target_storage", "project")))
        external_root = options.get("external_root")
        if storage not in {"project", "external", "user-data"}:
            raise StorageError("storage-layout requires a valid target storage")
        if storage == "external" and not external_root:
            raise StorageError("storage-layout external target requires external_root")
        layout = load_archledger_layout(root, require_registration=True)
        raw_plan = build_archledger_storage_migration_plan(
            root,
            storage=storage,
            external_root=str(external_root) if external_root else None,
        )
        return plan_for_storage_layout(
            root=root,
            layout=layout,
            target_storage=storage,
            external_root=str(external_root) if external_root else None,
            ledgercore_plan=storage_migration_plan_to_mapping(raw_plan),
        )

    def apply(
        self,
        root: Path,
        plan: ArchledgerMigrationPlan,
        *,
        dry_run: bool,
        reason: str,
    ) -> dict[str, Any]:
        layout = load_archledger_layout(root, require_registration=True)
        if plan.source is None:
            raise StorageError("storage-layout plan has no source fingerprint")
        issues = check_plan_staleness(plan, storage_layout_fingerprint(layout), root)
        if issues:
            raise StorageError(
                "Storage-layout plan is stale: " + "; ".join(issues),
                details={"code": "stale_plan"},
            )
        support = ledgercore_migration_support()
        payload = {
            "migration": self.name,
            "migration_id": plan.migration_id,
            "dry_run": dry_run,
            "reason": reason,
            "ledgercore_version": support.version,
            "capabilities": self._capability_payload(support),
            "source_storage": layout.data_storage,
            "target_storage": plan.destination.storage if plan.destination else None,
            "data_moved": False,
        }
        if not support.schema3_execution:
            payload.update(
                {
                    "supported": False,
                    "recovery_capability": "manual-intervention",
                    "reason_code": "ledgercore_executor_unavailable",
                    "remediation": [
                        "Install a Ledgercore release with schema-3 execution "
                        "and hooks.",
                        "Keep the current topology and do not move data manually.",
                    ],
                }
            )
            return payload

        raw = build_archledger_storage_migration_plan(
            root,
            storage=plan.destination.storage if plan.destination else "project",
            external_root=(plan.ledgercore_plan or {}).get("external_root")
            if plan.ledgercore_plan
            else None,
        )
        validation = validate_storage_migration_plan(raw, project_root=root)
        if not validation.valid:
            raise StorageError(
                "Ledgercore rejected the storage-layout plan: "
                + "; ".join(validation.errors),
                details={"code": "storage_conflict"},
            )
        if dry_run:
            payload.update({"supported": True, "validated": True})
            return payload
        result = execute_archledger_storage_migration(
            raw,
            project_root=root,
            quiescence_check=lambda: None,
            validate_staged=lambda _index: None,
            validate_activated=lambda _index: None,
            finalize=lambda: None,
        )
        receipt = create_receipt(
            plan.migration_id,
            self.name,
            layout.project_uuid,
            layout.project_uuid,
            plan.source.fingerprint,
            plan.source.fingerprint,
            [],
            [],
        )
        payload.update(
            {
                "supported": True,
                "validated": True,
                "data_moved": bool(result.items_completed),
                "journal_path": str(result.journal_path),
                "receipt_path": str(
                    write_receipt(
                        receipt, layout.tool_config_path.parent / "migrations"
                    )
                ),
            }
        )
        return payload

    def recover(self, root: Path, journal: Path, *, dry_run: bool) -> dict[str, Any]:
        support = ledgercore_migration_support()
        resolved_journal = journal.resolve(strict=False)
        allowed = {
            (root / ".ledger" / "migrations").resolve(strict=False),
            (root / ".ledger" / "archledger" / "migrations").resolve(strict=False),
        }
        if (
            journal.is_symlink()
            or not journal.is_file()
            or resolved_journal.parent not in allowed
        ):
            raise StorageError(
                "Migration journal is outside the trusted project journal directory."
            )
        inspected = inspect_storage_migration(resolved_journal)
        try:
            layout = load_archledger_layout(root, require_registration=True)
            if inspected.project_uuid != layout.project_uuid:
                raise StorageError(
                    "Migration journal project identity does not match the "
                    "current project.",
                    details={"code": "project_uuid_mismatch"},
                )
        except StorageError:
            raise
        except Exception:
            # A legacy/manual journal may be inspectable before the canonical
            # project exists; report it honestly rather than guessing identity.
            pass
        if not support.schema3_recovery:
            return {
                "migration": self.name,
                "journal": str(journal),
                "phase": inspected.phase,
                "dry_run": dry_run,
                "supported": False,
                "capability": inspected.recovery_capability,
                "reason": (
                    "The installed Ledgercore only supports completed-journal "
                    "inspection."
                ),
            }
        result = recover_storage_migration(journal)
        return {
            "migration": self.name,
            "journal": str(journal),
            "phase": result.phase,
            "dry_run": dry_run,
            "supported": True,
            "items_completed": result.items_completed,
        }

    def cleanup(
        self, root: Path, *, dry_run: bool, yes: bool, reason: str
    ) -> dict[str, Any]:
        del root, yes, reason
        return {
            "migration": self.name,
            "dry_run": dry_run,
            "supported": False,
            "reason": (
                "Storage-layout cleanup is not source cleanup; the source remains "
                "authoritative until activation succeeds."
            ),
        }

    @staticmethod
    def _capability_payload(support: Any) -> dict[str, Any]:
        return {
            "plan": True,
            "apply": support.schema3_execution,
            "inspect": support.public_api,
            "recover": support.schema3_recovery,
            "resume": support.resume,
            "rollback": support.rollback,
            "prepared_sources": support.prepared_sources,
        }


from archledger.migrations.registry import register_handler  # noqa: E402

register_handler(StorageLayoutHandler())
