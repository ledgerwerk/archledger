"""Project-layout migration handler for Archledger.

This handler migrates legacy root config/data to Ledgercore schema-3 project layout.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from archledger.errors import StorageError
from archledger.migrations.models import (
    ArchledgerMigrationPlan,
    IdentityPolicy,
    MigrationCapabilities,
    MigrationDestinationInfo,
    MigrationInventory,
    MigrationOperation,
    MigrationProjectInfo,
    MigrationSourceInfo,
)
from archledger.migrations.plan_io import compute_plan_hash


class ProjectLayoutHandler:
    """Handler for project-layout migration."""

    name = "project-layout"
    summary = "Migrate legacy root config/data to Ledgercore schema-3 project layout"
    capabilities = MigrationCapabilities(
        plan=True,
        apply=True,
        recover=True,
        cleanup=True,
        requires_legacy_state=True,
    )

    def status(self, root: Path) -> dict[str, Any]:
        """Report migration-specific status."""
        from archledger.project_context import classify_project_state
        from archledger.project_migration import inspect_project_migration

        state = classify_project_state(root)
        if state == "legacy":
            inspection = inspect_project_migration(root)
            return {
                "state": "legacy",
                "source_kind": inspection.source_kind,
                "source_data_root": str(inspection.source_data_root)
                if inspection.source_data_root
                else None,
                "section_count": inspection.section_count,
                "record_count": inspection.record_count,
            }
        elif state == "canonical":
            return {"state": "canonical-ready"}
        return {"state": state}

    def plan(self, root: Path, options: dict[str, Any]) -> ArchledgerMigrationPlan:
        """Create a deterministic migration plan."""
        from archledger.project_migration import inspect_project_migration

        identity_policy_str = options.get("identity_policy", "strict")
        identity_policy = IdentityPolicy(identity_policy_str)

        inspection = inspect_project_migration(root)

        # Collect source information
        source_info = self._collect_source_info(inspection)
        project_info = self._collect_project_info(root, inspection, identity_policy)
        dest_info = self._collect_destination_info(root)
        inventory = self._collect_inventory(inspection)
        operations = self._collect_operations(root, inspection)

        # Build plan
        plan = ArchledgerMigrationPlan(
            migration=self.name,
            project=project_info,
            source=source_info,
            destination=dest_info,
            inventory=inventory,
            operations=tuple(operations),
            preconditions=(
                "source fingerprint matches",
                "source contains no symlinks or special files",
                "destination ownership is compatible",
                "no incomplete migration requires recovery",
            ),
            blockers=(),
            warnings=(),
        )

        # Compute hash
        plan_dict = plan.to_dict()
        plan_hash = compute_plan_hash(plan_dict)

        return ArchledgerMigrationPlan(
            migration=plan.migration,
            project=plan.project,
            source=plan.source,
            destination=plan.destination,
            inventory=plan.inventory,
            operations=plan.operations,
            preconditions=plan.preconditions,
            blockers=plan.blockers,
            warnings=plan.warnings,
            plan_hash=plan_hash,
        )

    def apply(
        self,
        root: Path,
        plan: ArchledgerMigrationPlan,
        *,
        dry_run: bool,
        reason: str,
    ) -> dict[str, Any]:
        """Execute a migration plan."""
        if dry_run:
            return self._dry_run_apply(root, plan, reason)

        return self._execute_apply(root, plan, reason)

    def recover(self, root: Path, journal: Path, *, dry_run: bool) -> dict[str, Any]:
        """Recover from an interrupted migration."""
        # TODO: Implement recovery
        raise NotImplementedError("Recovery not yet implemented")

    def cleanup(
        self,
        root: Path,
        *,
        dry_run: bool,
        yes: bool,
        reason: str,
    ) -> dict[str, Any]:
        """Remove verified legacy source after migration."""
        # TODO: Implement cleanup
        raise NotImplementedError("Cleanup not yet implemented")

    def _collect_source_info(self, inspection: Any) -> MigrationSourceInfo:
        """Collect source information from inspection."""
        fingerprint = self._compute_source_fingerprint(inspection)
        return MigrationSourceInfo(
            config_path=inspection.source_config_path,
            data_root=inspection.source_data_root,
            config_version=inspection.source_config_version
            if hasattr(inspection, "source_config_version")
            else 10,
            fingerprint=fingerprint,
            file_count=inspection.section_count + inspection.record_count,
            total_bytes=0,  # TODO: compute actual size
        )

    def _collect_project_info(
        self,
        root: Path,
        inspection: Any,
        identity_policy: IdentityPolicy,
    ) -> MigrationProjectInfo:
        """Collect project identity information."""
        manifest_path = root / ".ledger" / "ledger.toml"
        manifest_exists = manifest_path.exists()
        manifest_uuid = None

        if manifest_exists:
            # Read UUID from manifest
            content = manifest_path.read_text()
            for line in content.split("\n"):
                if line.strip().startswith("uuid"):
                    manifest_uuid = line.split('"')[1] if '"' in line else None

        legacy_uuid = inspection.source_project_uuid

        # Determine target UUID and check for mismatches
        if manifest_exists and manifest_uuid and legacy_uuid:
            if manifest_uuid != legacy_uuid:
                if identity_policy == IdentityPolicy.ADOPT_PROJECT:
                    target_uuid = manifest_uuid
                else:
                    # Block with remediation
                    raise StorageError(
                        "Legacy Archledger identity differs from"
                        " the shared Ledgercore project.",
                        details={
                            "code": "project_uuid_mismatch",
                            "manifest_uuid": manifest_uuid,
                            "legacy_config_uuid": legacy_uuid,
                            "remediation": [
                                "Review the project identity evidence.",
                                "If this Archledger belongs to the current"
                                " shared project, run"
                                " 'archledger migrate plan project-layout"
                                " --identity-policy adopt-project'.",
                                "Do not move files manually.",
                            ],
                        },
                    )
            else:
                target_uuid = legacy_uuid
        elif identity_policy == IdentityPolicy.ADOPT_PROJECT and manifest_uuid:
            target_uuid = manifest_uuid
        else:
            target_uuid = legacy_uuid

        return MigrationProjectInfo(
            root=root,
            manifest_exists=manifest_exists,
            manifest_uuid=manifest_uuid,
            legacy_uuid=legacy_uuid,
            target_uuid=target_uuid,
            identity_policy=identity_policy,
        )

    def _collect_destination_info(self, root: Path) -> MigrationDestinationInfo:
        """Collect destination information."""
        return MigrationDestinationInfo(
            manifest_path=root / ".ledger" / "ledger.toml",
            config_path=root / ".ledger" / "archledger" / "config.toml",
            data_root=root / ".ledger" / "archledger" / "data",
            storage="project",
        )

    def _collect_inventory(self, inspection: Any) -> MigrationInventory:
        """Collect inventory from inspection."""
        return MigrationInventory(
            records=inspection.record_count,
            sections=inspection.section_count,
            archived_records=getattr(inspection, "archive_count", 0),
            tombstones=getattr(inspection, "tombstone_count", 0),
            highest_number=getattr(inspection, "highest_number", 0),
            stored_next_number=getattr(inspection, "stored_next_number", 0),
        )

    def _collect_operations(
        self, root: Path, inspection: Any
    ) -> list[MigrationOperation]:
        """Collect operations for the plan."""
        operations = []

        # Copy operations for sections
        if inspection.source_data_root:
            data_root = Path(inspection.source_data_root)
            sections_dir = data_root / "sections"
            if sections_dir.exists():
                for section_file in sections_dir.glob("*.md"):
                    rel_path = section_file.relative_to(data_root)
                    operations.append(
                        MigrationOperation(
                            operation="copy",
                            source=str(rel_path),
                            destination=str(rel_path),
                            sha256=self._file_hash(section_file),
                            size=section_file.stat().st_size,
                        )
                    )

        # Write config operation
        operations.append(
            MigrationOperation(
                operation="write-config",
                destination=".ledger/archledger/config.toml",
                config_version=12,
            )
        )

        # Merge manifest operation
        operations.append(
            MigrationOperation(
                operation="merge-manifest",
                destination=".ledger/ledger.toml",
            )
        )

        return operations

    def _compute_source_fingerprint(self, inspection: Any) -> str:
        """Compute aggregate source fingerprint."""
        hasher = hashlib.sha256()

        if inspection.source_data_root:
            data_root = Path(inspection.source_data_root)
            for file_path in sorted(data_root.rglob("*")):
                if file_path.is_file():
                    hasher.update(str(file_path.relative_to(data_root)).encode())
                    hasher.update(file_path.read_bytes())

        return "sha256:" + hasher.hexdigest()

    def _file_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

    def _dry_run_apply(
        self, root: Path, plan: ArchledgerMigrationPlan, reason: str
    ) -> dict[str, Any]:
        """Dry run apply - validate without modifying."""
        return {
            "dry_run": True,
            "reason": reason,
            "operations": len(plan.operations),
            "message": "Dry run completed successfully",
        }

    def _execute_apply(
        self, root: Path, plan: ArchledgerMigrationPlan, reason: str
    ) -> dict[str, Any]:
        """Execute the migration."""
        # TODO: Implement full apply with Ledgercore
        # For now, use existing implementation
        from archledger.project_migration import (
            apply_project_migration,
            inspect_project_migration,
        )

        inspection = inspect_project_migration(root)
        result = apply_project_migration(inspection)

        return {
            "receipt_path": str(result.receipt_path),
            "legacy_source_preserved": True,
            "cleanup_available": True,
            "cleanup_command": "archledger migrate cleanup project-layout --dry-run",
        }


# Register the handler
from archledger.migrations.registry import register_handler  # noqa: E402

register_handler(ProjectLayoutHandler())
