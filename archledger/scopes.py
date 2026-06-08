"""Record scope normalization and matching for monorepo applicability.

Scope is a record-level metadata block that declares which addon, addon
group, integration, subsystem, or whole monorepo a record applies to.  It
is separate from ``source_refs``, which drive drift detection and
implementation linkage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archledger.source_refs import validate_relative_posix_path

VALID_SCOPE_KINDS: frozenset[str] = frozenset(
    {
        "monorepo",
        "addon",
        "addon_group",
        "integration",
        "subsystem",
    }
)

VALID_SCOPE_LIFECYCLES: frozenset[str] = frozenset(
    {
        "active",
        "deprecated",
        "retired",
    }
)


@dataclass(frozen=True, slots=True)
class RecordScope:
    kind: str
    name: str
    applies_to: tuple[str, ...]
    excludes: tuple[str, ...] = ()
    lifecycle: str = "active"


def normalize_scope(
    record_id: str,
    value: object,
    *,
    workspace_root: Path | None = None,
) -> tuple[RecordScope | None, list[str]]:
    """Normalize the ``scope`` front-matter value for *record_id*.

    Returns ``(scope, warnings)``.  When *value* is ``None``, returns
    ``(None, [])``.
    """
    if value is None:
        return None, []

    if not isinstance(value, dict):
        return None, [f"Record {record_id} scope must be a mapping."]

    warnings: list[str] = []

    raw_kind = value.get("kind")
    if not isinstance(raw_kind, str) or not raw_kind.strip():
        return None, [f"Record {record_id} scope.kind must be a non-empty string."]
    kind = raw_kind.strip()
    if kind not in VALID_SCOPE_KINDS:
        return None, [
            f"Record {record_id} scope.kind {kind!r} is not allowed. "
            f"Allowed: {', '.join(sorted(VALID_SCOPE_KINDS))}"
        ]

    raw_name = value.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        return None, [f"Record {record_id} scope.name must be a non-empty string."]
    name = raw_name.strip()

    raw_applies_to = value.get("applies_to")
    if not isinstance(raw_applies_to, list) or not raw_applies_to:
        return None, [
            f"Record {record_id} scope.applies_to must be a non-empty list."
        ]
    raw_lifecycle = value.get("lifecycle", "active")
    if not isinstance(raw_lifecycle, str) or not raw_lifecycle.strip():
        return None, [
            f"Record {record_id} scope.lifecycle must be a non-empty string."
        ]
    lifecycle = raw_lifecycle.strip()
    if lifecycle not in VALID_SCOPE_LIFECYCLES:
        return None, [
            f"Record {record_id} scope.lifecycle {lifecycle!r} is not allowed. "
            f"Allowed: {', '.join(sorted(VALID_SCOPE_LIFECYCLES))}"
        ]

    applies_to: list[str] = []
    for i, entry in enumerate(raw_applies_to, start=1):
        if not isinstance(entry, str) or not entry.strip():
            return None, [
                f"Record {record_id} scope.applies_to entry {i} "
                "must be a non-empty string."
            ]
        original = entry.strip()
        is_dir = original.endswith("/")
        path_text = original.rstrip("/") if is_dir else original
        try:
            validated = validate_relative_posix_path(
                path_text,
                field_name=f"Record {record_id} scope.applies_to entry {i}",
            )
        except ValueError as exc:
            return None, [str(exc)]
        if is_dir:
            validated = f"{validated}/"

        if workspace_root is not None and lifecycle != "retired":
            abs_path = workspace_root / (validated.rstrip("/"))
            if is_dir and not abs_path.is_dir():
                warnings.append(
                    f"Record {record_id} scope.applies_to entry {i} "
                    f"directory does not exist: {validated}"
                )
            elif not is_dir and not abs_path.exists():
                warnings.append(
                    f"Record {record_id} scope.applies_to entry {i} "
                    f"path does not exist: {validated}"
                )

        applies_to.append(validated)

    raw_excludes = value.get("excludes", [])
    excludes: list[str] = []
    if raw_excludes is not None:
        if not isinstance(raw_excludes, list):
            return None, [
                f"Record {record_id} scope.excludes must be a list."
            ]
        for i, entry in enumerate(raw_excludes, start=1):
            if not isinstance(entry, str) or not entry.strip():
                return None, [
                    f"Record {record_id} scope.excludes entry {i} "
                    "must be a non-empty string."
                ]
            original = entry.strip()
            is_dir = original.endswith("/")
            path_text = original.rstrip("/") if is_dir else original
            try:
                validated = validate_relative_posix_path(
                    path_text,
                    field_name=f"Record {record_id} scope.excludes entry {i}",
                )
            except ValueError as exc:
                return None, [str(exc)]
            if is_dir:
                validated = f"{validated}/"
            excludes.append(validated)


    return (
        RecordScope(
            kind=kind,
            name=name,
            applies_to=tuple(applies_to),
            excludes=tuple(excludes),
            lifecycle=lifecycle,
        ),
        warnings,
    )


def scope_matches_path(scope: RecordScope, path: str) -> bool:
    """Return True if *path* falls within *scope*'s applicability.

    A path matches when it is covered by ``scope.applies_to`` and not
    covered by ``scope.excludes``.  Directory entries (ending in ``/``)
    are treated as recursive prefixes.
    """
    for excluded in scope.excludes:
        excluded_stripped = excluded.rstrip("/")
        if path.startswith(excluded_stripped):
            # Exact file match or directory prefix match.
            if path == excluded_stripped or excluded.endswith("/"):
                return False
    for applies in scope.applies_to:
        applies_stripped = applies.rstrip("/")
        if path == applies_stripped or (
            path.startswith(applies_stripped) and applies.endswith("/")
        ):
            return True
    return False


__all__ = [
    "VALID_SCOPE_KINDS",
    "VALID_SCOPE_LIFECYCLES",
    "RecordScope",
    "normalize_scope",
    "scope_matches_path",
]
