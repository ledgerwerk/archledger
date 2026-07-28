"""Canonical identity-ledgercore domain migration handler."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from archledger.identity_migration import migrate_identity
from archledger.migrations.domain_helpers import (
    file_digest,
    plan_for_domain,
    relative_operations,
    validate_domain_plan,
)
from archledger.migrations.models import (
    ArchledgerMigrationPlan,
    MigrationCapabilities,
    MigrationOperation,
)
from archledger.migrations.receipts import create_receipt, write_receipt
from archledger.storage.paths import resolve_project_paths


class IdentityLedgercoreHandler:
    """Rewrite legacy IDs and refs using the existing domain service."""

    name = "identity-ledgercore"
    summary = "Migrate legacy Archledger IDs to Ledgercore local IDs and global refs"
    capabilities = MigrationCapabilities(
        plan=True,
        apply=True,
        recover=False,
        cleanup=False,
        requires_legacy_state=False,
        requires_project_layout=True,
    )

    def status(self, root: Path) -> dict[str, Any]:
        try:
            paths, _config, _warnings = resolve_project_paths(root)
        except Exception:
            return {"state": "requires-project-layout"}
        return {"state": "available", "config_path": str(paths.config_path)}

    def plan(self, root: Path, options: dict[str, Any]) -> ArchledgerMigrationPlan:
        del options
        paths, config, _warnings = resolve_project_paths(root)
        operations = relative_operations(
            paths,
            lambda path: MigrationOperation(
                operation="rewrite",
                source=path.relative_to(paths.workspace_root).as_posix(),
                destination=path.relative_to(paths.workspace_root).as_posix(),
                sha256=file_digest(path),
                reason="rewrite IDs and refs to Ledgercore format",
            ),
        )
        return plan_for_domain(
            migration=self.name,
            paths=paths,
            config=config,
            operations=operations,
        )

    def apply(
        self,
        root: Path,
        plan: ArchledgerMigrationPlan,
        *,
        dry_run: bool,
        reason: str,
    ) -> dict[str, Any]:
        paths, config, _warnings = resolve_project_paths(root)
        validate_domain_plan(plan, paths, config)
        result = migrate_identity(paths, config, apply=not dry_run)
        payload = {
            "migration": self.name,
            "migration_id": plan.migration_id,
            "dry_run": dry_run,
            "reason": reason,
            "migrated_count": len(result.migrated),
            "rewritten_count": len(result.rewritten),
            "source_fingerprint": plan.source.fingerprint if plan.source else None,
            "recovery_capability": "manual-intervention",
        }
        if not dry_run:
            receipt = create_receipt(
                plan.migration_id,
                self.name,
                config.project_uuid,
                config.project_uuid,
                plan.source.fingerprint if plan.source else "",
                plan.source.fingerprint if plan.source else "",
                [item.new_path.as_posix() for item in result.migrated],
                [item.path.as_posix() for item in result.rewritten],
            )
            payload["receipt_path"] = str(
                write_receipt(receipt, paths.archledger_dir / "migrations")
            )
        return payload

    def recover(self, root: Path, journal: Path, *, dry_run: bool) -> dict[str, Any]:
        return {
            "migration": self.name,
            "journal": str(journal),
            "dry_run": dry_run,
            "capability": "manual-intervention",
            "supported": False,
        }

    def cleanup(
        self, root: Path, *, dry_run: bool, yes: bool, reason: str
    ) -> dict[str, Any]:
        del root, yes, reason
        return {
            "migration": self.name,
            "dry_run": dry_run,
            "supported": False,
            "reason": "identity migration has no legacy source cleanup operation",
        }


from archledger.migrations.registry import register_handler  # noqa: E402

register_handler(IdentityLedgercoreHandler())
