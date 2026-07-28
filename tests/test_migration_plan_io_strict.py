"""Strict migration plan round-trip and precondition tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from archledger.migrations.models import (
    ArchledgerMigrationPlan,
    MigrationDestinationInfo,
    MigrationOperation,
    MigrationProjectInfo,
    MigrationSourceInfo,
)
from archledger.migrations.plan_io import (
    check_plan_staleness,
    compute_plan_hash,
    load_plan,
    save_plan,
    validate_plan_schema,
)


def _plan(root: Path) -> ArchledgerMigrationPlan:
    digest = "sha256:" + "a" * 64
    return ArchledgerMigrationPlan(
        migration="storage-layout",
        migration_id="migration-test-0001",
        project=MigrationProjectInfo(
            root=root.resolve(),
            manifest_exists=True,
            manifest_uuid="project-uuid",
            legacy_uuid=None,
            target_uuid="project-uuid",
        ),
        source=MigrationSourceInfo(
            config_path=(root / "source.toml").resolve(),
            data_root=(root / "source").resolve(),
            config_version=12,
            fingerprint=digest,
            file_count=1,
            total_bytes=3,
        ),
        destination=MigrationDestinationInfo(
            manifest_path=(root / ".ledger" / "ledger.toml").resolve(),
            config_path=(root / ".ledger" / "archledger" / "config.toml").resolve(),
            data_root=(root / ".ledger" / "archledger" / "data").resolve(),
            storage="project",
        ),
        operations=(
            MigrationOperation(
                operation="copy",
                source="records/adr-0001.md",
                destination="records/adr-0001.md",
                sha256=digest,
                size=3,
                destination_policy="create-only",
            ),
        ),
        preconditions=("source fingerprint matches",),
        required_hooks=("validate_staged",),
        cleanup_policy={"source_deletion": False},
    )


def test_plan_v2_round_trip_preserves_every_field(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    path = tmp_path / "plan.json"
    save_plan(plan, path)
    loaded = load_plan(path)
    original = json.loads(path.read_text(encoding="utf-8"))
    assert loaded.to_dict() == original
    assert loaded.ledgercore_plan is None
    assert loaded.required_hooks == ("validate_staged",)
    assert loaded.cleanup_policy == {"source_deletion": False}


def test_plan_hash_is_deterministic(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    mapping = plan.to_dict()
    assert compute_plan_hash(mapping) == compute_plan_hash(
        dict(reversed(mapping.items()))
    )


def test_plan_parser_rejects_unknown_schema_and_fields(tmp_path: Path) -> None:
    plan = _plan(tmp_path).to_dict()
    plan["plan_hash"] = compute_plan_hash(plan)
    plan["unknown"] = True
    assert any("unknown field" in item for item in validate_plan_schema(plan))
    plan.pop("unknown")
    plan["schema"] = "archledger.migration-plan.v99"
    plan["plan_hash"] = compute_plan_hash(plan)
    with pytest.raises(ValueError, match="unsupported plan schema"):
        load_path = tmp_path / "invalid.json"
        load_path.write_text(json.dumps(plan), encoding="utf-8")
        load_plan(load_path)


def test_plan_parser_rejects_path_traversal(tmp_path: Path) -> None:
    plan = _plan(tmp_path).to_dict()
    plan["operations"][0]["source"] = "../outside.md"
    plan["plan_hash"] = compute_plan_hash(plan)
    path = tmp_path / "unsafe.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="safe relative path"):
        load_plan(path)


def test_staleness_checks_source_and_project_root(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    assert check_plan_staleness(plan, "sha256:" + "b" * 64, tmp_path) == [
        "Source fingerprint has changed since plan was created"
    ]
    assert check_plan_staleness(plan, plan.source.fingerprint, tmp_path / "other") == [
        "Plan was created for a different root directory"
    ]
