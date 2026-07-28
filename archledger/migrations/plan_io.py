"""Strict deterministic serialization for Archledger migration plans."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from archledger.migrations.models import (
    ArchledgerMigrationPlan,
    IdentityPolicy,
    MigrationDestinationInfo,
    MigrationInventory,
    MigrationOperation,
    MigrationProjectInfo,
    MigrationSourceInfo,
)

PLAN_SCHEMA = "archledger.migration-plan.v2"
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def compute_plan_hash(plan_dict: Mapping[str, Any]) -> str:
    """Compute the SHA-256 hash of all plan content except ``plan_hash``."""
    plan_copy = {key: value for key, value in plan_dict.items() if key != "plan_hash"}
    serialized = json.dumps(
        plan_copy,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_plan_hash(plan_dict: Mapping[str, Any]) -> bool:
    """Return whether a persisted plan hash matches its full content."""
    expected_hash = plan_dict.get("plan_hash")
    return isinstance(expected_hash, str) and expected_hash == compute_plan_hash(
        plan_dict
    )


def save_plan(plan: ArchledgerMigrationPlan, output_path: Path) -> None:
    """Persist a complete plan with canonical JSON and a deterministic hash."""
    plan_dict = plan.to_dict()
    plan_dict["plan_hash"] = compute_plan_hash(plan_dict)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(plan_dict, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_plan(plan_path: Path) -> ArchledgerMigrationPlan:
    """Load and strictly validate a persisted v2 plan."""
    if plan_path.is_symlink() or not plan_path.is_file():
        raise ValueError(f"Plan file is missing or not a regular file: {plan_path}")
    try:
        document = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read migration plan: {exc}") from exc
    if not isinstance(document, Mapping):
        raise ValueError("Migration plan root must be a JSON object")
    errors = validate_plan_schema(document)
    if errors:
        raise ValueError("Invalid migration plan: " + "; ".join(errors))
    if not validate_plan_hash(document):
        raise ValueError("Plan hash mismatch - plan may have been tampered with")
    return plan_from_mapping(document)


def plan_from_mapping(document: Mapping[str, Any]) -> ArchledgerMigrationPlan:
    """Reconstruct every typed plan field without lossy simplification."""
    errors = validate_plan_schema(document)
    if errors:
        raise ValueError("Invalid migration plan: " + "; ".join(errors))

    project = _project_from_mapping(document.get("project"))
    source = _source_from_mapping(document.get("source"))
    destination = _destination_from_mapping(document.get("destination"))
    inventory = _inventory_from_mapping(document.get("inventory"))
    operations_raw = _sequence(document.get("operations"), "operations")
    operations = tuple(_operation_from_mapping(item) for item in operations_raw)
    ledgercore_plan = document.get("ledgercore_plan")
    if ledgercore_plan is not None and not isinstance(ledgercore_plan, Mapping):
        raise ValueError("ledgercore_plan must be an object or null")
    cleanup_policy = document.get("cleanup_policy")
    if cleanup_policy is not None and not isinstance(cleanup_policy, Mapping):
        raise ValueError("cleanup_policy must be an object or null")
    migration_id = str(document.get("migration_id") or _derive_migration_id(document))
    return ArchledgerMigrationPlan(
        schema=str(document["schema"]),
        migration=str(document["migration"]),
        tool=str(document["tool"]),
        migration_id=migration_id,
        project=project,
        source=source,
        destination=destination,
        inventory=inventory,
        operations=operations,
        preconditions=tuple(_strings(document.get("preconditions"), "preconditions")),
        blockers=tuple(_strings(document.get("blockers"), "blockers")),
        warnings=tuple(_strings(document.get("warnings"), "warnings")),
        ledgercore_plan=dict(ledgercore_plan) if ledgercore_plan is not None else None,
        required_hooks=tuple(
            _strings(document.get("required_hooks"), "required_hooks")
        ),
        cleanup_policy=dict(cleanup_policy) if cleanup_policy is not None else None,
        plan_hash=str(document["plan_hash"]),
    )


def validate_plan_schema(plan_dict: Mapping[str, Any]) -> list[str]:
    """Validate strict v2 shape, paths, fingerprints, and nested fields."""
    errors: list[str] = []
    allowed = {
        "schema",
        "migration",
        "tool",
        "migration_id",
        "project",
        "source",
        "destination",
        "inventory",
        "operations",
        "preconditions",
        "blockers",
        "warnings",
        "ledgercore_plan",
        "required_hooks",
        "cleanup_policy",
        "plan_hash",
    }
    errors.extend(_unknown_fields(plan_dict, allowed, "plan"))
    if plan_dict.get("schema") != PLAN_SCHEMA:
        errors.append(f"unsupported plan schema: {plan_dict.get('schema')!r}")
    if not isinstance(plan_dict.get("migration"), str) or not plan_dict.get(
        "migration"
    ):
        errors.append("missing migration name")
    if plan_dict.get("tool") != "archledger":
        errors.append("tool must be archledger")
    migration_id = plan_dict.get("migration_id")
    if migration_id is not None and (
        not isinstance(migration_id, str) or not migration_id
    ):
        errors.append("migration_id must be a non-empty string when present")
    plan_hash = plan_dict.get("plan_hash")
    if not isinstance(plan_hash, str) or not _SHA256.fullmatch(plan_hash):
        errors.append("plan_hash must be a sha256 digest")
    for field in (
        "operations",
        "preconditions",
        "blockers",
        "warnings",
        "required_hooks",
    ):
        if field in plan_dict and not isinstance(plan_dict[field], list):
            errors.append(f"{field} must be an array")
    for field in ("project", "source", "destination", "inventory"):
        value = plan_dict.get(field)
        if value is not None and not isinstance(value, Mapping):
            errors.append(f"{field} must be an object or null")
    if isinstance(plan_dict.get("project"), Mapping):
        errors.extend(_validate_project_mapping(plan_dict["project"]))
    if isinstance(plan_dict.get("source"), Mapping):
        errors.extend(_validate_source_mapping(plan_dict["source"]))
    if isinstance(plan_dict.get("destination"), Mapping):
        errors.extend(_validate_destination_mapping(plan_dict["destination"]))
    if isinstance(plan_dict.get("inventory"), Mapping):
        errors.extend(
            _unknown_fields(
                plan_dict["inventory"],
                {
                    "records",
                    "sections",
                    "archived_records",
                    "tombstones",
                    "highest_number",
                    "stored_next_number",
                },
                "inventory",
            )
        )
    operations = plan_dict.get("operations")
    if isinstance(operations, list):
        for index, operation in enumerate(operations):
            if not isinstance(operation, Mapping):
                errors.append(f"operations[{index}] must be an object")
                continue
            errors.extend(_validate_operation_mapping(operation, index))
    return errors


def check_plan_staleness(
    plan: ArchledgerMigrationPlan,
    current_fingerprint: str,
    current_root: Path,
) -> list[str]:
    """Compare current domain source/root state with a persisted plan."""
    issues: list[str] = []
    if plan.source and plan.source.fingerprint != current_fingerprint:
        issues.append("Source fingerprint has changed since plan was created")
    if plan.project and plan.project.root.resolve(strict=False) != current_root.resolve(
        strict=False
    ):
        issues.append("Plan was created for a different root directory")
    return issues


def _project_from_mapping(value: object) -> MigrationProjectInfo | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("project must be an object")
    return MigrationProjectInfo(
        root=_absolute_path(value["root"], "project.root"),
        manifest_exists=bool(value["manifest_exists"]),
        manifest_uuid=_optional_string(
            value.get("manifest_uuid"), "project.manifest_uuid"
        ),
        legacy_uuid=_optional_string(value.get("legacy_uuid"), "project.legacy_uuid"),
        target_uuid=_optional_string(value.get("target_uuid"), "project.target_uuid"),
        identity_policy=IdentityPolicy(str(value.get("identity_policy", "strict"))),
    )


def _source_from_mapping(value: object) -> MigrationSourceInfo | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("source must be an object")
    return MigrationSourceInfo(
        config_path=_optional_absolute_path(
            value.get("config_path"), "source.config_path"
        ),
        data_root=_optional_absolute_path(value.get("data_root"), "source.data_root"),
        config_version=int(value["config_version"]),
        fingerprint=_fingerprint(value["fingerprint"], "source.fingerprint"),
        file_count=int(value["file_count"]),
        total_bytes=int(value["total_bytes"]),
    )


def _destination_from_mapping(value: object) -> MigrationDestinationInfo | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("destination must be an object")
    return MigrationDestinationInfo(
        manifest_path=_absolute_path(
            value["manifest_path"], "destination.manifest_path"
        ),
        config_path=_absolute_path(value["config_path"], "destination.config_path"),
        data_root=_absolute_path(value["data_root"], "destination.data_root"),
        storage=str(value["storage"]),
    )


def _inventory_from_mapping(value: object) -> MigrationInventory | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("inventory must be an object")
    return MigrationInventory(
        **{
            field: int(value[field])
            for field in (
                "records",
                "sections",
                "archived_records",
                "tombstones",
                "highest_number",
                "stored_next_number",
            )
        }
    )


def _operation_from_mapping(value: Mapping[str, Any]) -> MigrationOperation:
    return MigrationOperation(
        operation=str(value["operation"]),
        source=_optional_string(value.get("source"), "operation.source"),
        destination=str(value["destination"]),
        sha256=_optional_string(value.get("sha256"), "operation.sha256"),
        size=int(value["size"]) if value.get("size") is not None else None,
        reason=_optional_string(value.get("reason"), "operation.reason"),
        config_version=int(value["config_version"])
        if value.get("config_version") is not None
        else None,
        before_fingerprint=_optional_string(
            value.get("before_fingerprint"), "operation.before_fingerprint"
        ),
        target_fingerprint=_optional_string(
            value.get("target_fingerprint"), "operation.target_fingerprint"
        ),
        destination_policy=_optional_string(
            value.get("destination_policy"), "operation.destination_policy"
        ),
        hook=_optional_string(value.get("hook"), "operation.hook"),
    )


def _validate_project_mapping(value: Mapping[str, Any]) -> list[str]:
    allowed = {
        "root",
        "manifest_exists",
        "manifest_uuid",
        "legacy_uuid",
        "target_uuid",
        "identity_policy",
    }
    return _unknown_fields(value, allowed, "project") + _required(
        value,
        allowed - {"manifest_uuid", "legacy_uuid", "target_uuid", "identity_policy"},
        "project",
    )


def _validate_source_mapping(value: Mapping[str, Any]) -> list[str]:
    allowed = {
        "config_path",
        "data_root",
        "config_version",
        "fingerprint",
        "file_count",
        "total_bytes",
    }
    return _unknown_fields(value, allowed, "source") + _required(
        value, allowed - {"config_path", "data_root"}, "source"
    )


def _validate_destination_mapping(value: Mapping[str, Any]) -> list[str]:
    allowed = {"manifest_path", "config_path", "data_root", "storage"}
    return _unknown_fields(value, allowed, "destination") + _required(
        value, allowed, "destination"
    )


def _validate_operation_mapping(value: Mapping[str, Any], index: int) -> list[str]:
    allowed = {
        "operation",
        "source",
        "destination",
        "sha256",
        "size",
        "reason",
        "config_version",
        "before_fingerprint",
        "target_fingerprint",
        "destination_policy",
        "hook",
    }
    prefix = f"operations[{index}]"
    errors = _unknown_fields(value, allowed, prefix) + _required(
        value, {"operation", "destination"}, prefix
    )
    source = value.get("source")
    destination = value.get("destination")
    for name, path in (("source", source), ("destination", destination)):
        if path is not None and (
            not isinstance(path, str)
            or Path(path).is_absolute()
            or ".." in Path(path).parts
        ):
            errors.append(f"{prefix}.{name} must be a safe relative path")
    for name in ("sha256", "before_fingerprint", "target_fingerprint"):
        if value.get(name) is not None:
            try:
                _fingerprint(value[name], f"{prefix}.{name}")
            except ValueError as exc:
                errors.append(str(exc))
    return errors


def _unknown_fields(
    value: Mapping[str, Any], allowed: set[str], prefix: str
) -> list[str]:
    return [
        f"{prefix} contains unknown field: {key}"
        for key in sorted(set(value) - allowed)
    ]


def _required(value: Mapping[str, Any], fields: set[str], prefix: str) -> list[str]:
    return [
        f"{prefix} is missing required field: {field}"
        for field in sorted(fields)
        if field not in value
    ]


def _sequence(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def _strings(value: object, field: str) -> list[str]:
    items = _sequence(value if value is not None else [], field)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{field} must contain only strings")
    return [str(item) for item in items]


def _absolute_path(value: object, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be an absolute path")
    path = Path(value)
    if not path.is_absolute() or path != path.resolve(strict=False):
        raise ValueError(f"{field} must be canonical absolute path")
    return path


def _optional_absolute_path(value: object, field: str) -> Path | None:
    return None if value is None else _absolute_path(value, field)


def _optional_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string or null")
    return value


def _fingerprint(value: object, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{field} must be a sha256 digest")
    return value


def _derive_migration_id(document: Mapping[str, Any]) -> str:
    content = {
        key: value
        for key, value in document.items()
        if key not in {"plan_hash", "migration_id"}
    }
    return (
        "migration-"
        + hashlib.sha256(
            json.dumps(
                content, sort_keys=True, separators=(",", ":"), default=str
            ).encode("utf-8")
        ).hexdigest()[:24]
    )


__all__ = [
    "PLAN_SCHEMA",
    "check_plan_staleness",
    "compute_plan_hash",
    "load_plan",
    "plan_from_mapping",
    "save_plan",
    "validate_plan_hash",
    "validate_plan_schema",
]
