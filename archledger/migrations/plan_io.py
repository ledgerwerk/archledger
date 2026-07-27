"""Plan I/O for Archledger migration.

This module handles plan serialization, hashing, validation, and file loading.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from archledger.migrations.models import ArchledgerMigrationPlan


def compute_plan_hash(plan_dict: dict[str, Any]) -> str:
    """Compute deterministic hash of a plan dictionary.

    The hash is computed on the plan without the plan_hash field.
    """
    # Create a copy without plan_hash
    plan_copy = {k: v for k, v in plan_dict.items() if k != "plan_hash"}

    # Sort keys for deterministic serialization
    serialized = json.dumps(plan_copy, sort_keys=True, separators=(",", ":"))

    # Compute SHA-256
    return "sha256:" + hashlib.sha256(serialized.encode()).hexdigest()


def validate_plan_hash(plan_dict: dict[str, Any]) -> bool:
    """Validate that a plan's hash matches its content."""
    expected_hash = plan_dict.get("plan_hash")
    if not expected_hash:
        return False

    computed_hash = compute_plan_hash(plan_dict)
    return expected_hash == computed_hash


def save_plan(plan: ArchledgerMigrationPlan, output_path: Path) -> None:
    """Save a plan to a file."""
    plan_dict = plan.to_dict()
    # Ensure hash is computed
    if not plan.plan_hash:
        plan_dict["plan_hash"] = compute_plan_hash(plan_dict)

    output_path.write_text(json.dumps(plan_dict, indent=2, sort_keys=False))


def load_plan(plan_path: Path) -> ArchledgerMigrationPlan:
    """Load a plan from a file and validate it."""
    if not plan_path.exists():
        raise ValueError(f"Plan file not found: {plan_path}")

    content = plan_path.read_text()
    plan_dict = json.loads(content)

    # Validate schema
    schema = plan_dict.get("schema")
    if schema != "archledger.migration-plan.v1":
        raise ValueError(f"Unknown plan schema: {schema}")

    # Validate hash
    if not validate_plan_hash(plan_dict):
        raise ValueError("Plan hash mismatch - plan may have been tampered with")

    # Reconstruct plan (simplified - full implementation would reconstruct all objects)
    return ArchledgerMigrationPlan(
        schema=plan_dict["schema"],
        migration=plan_dict.get("migration", ""),
        tool=plan_dict.get("tool", "archledger"),
        plan_hash=plan_dict.get("plan_hash", ""),
    )


def validate_plan_schema(plan_dict: dict[str, Any]) -> list[str]:
    """Validate a plan dictionary against the schema.

    Returns a list of validation errors.
    """
    errors = []

    if plan_dict.get("schema") != "archledger.migration-plan.v1":
        errors.append("Invalid or missing schema")

    if not plan_dict.get("migration"):
        errors.append("Missing migration name")

    if not plan_dict.get("tool"):
        errors.append("Missing tool name")

    if not plan_dict.get("plan_hash"):
        errors.append("Missing plan hash")

    return errors


def check_plan_staleness(
    plan: ArchledgerMigrationPlan,
    current_fingerprint: str,
    current_root: Path,
) -> list[str]:
    """Check if a plan is stale.

    Returns a list of staleness reasons.
    """
    issues = []

    if plan.source and plan.source.fingerprint != current_fingerprint:
        issues.append("Source fingerprint has changed since plan was created")

    if plan.project and plan.project.root != current_root:
        issues.append("Plan was created for a different root directory")

    return issues
