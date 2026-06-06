"""Executable test reference normalization and validation.

Test refs link records to test files or test node IDs (e.g.
``tests/test_discounts.py::test_expired``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archledger.source_refs import validate_relative_posix_path


@dataclass(frozen=True, slots=True)
class TestRef:
    path: str
    nodeid: str = ""
    role: str = "validates"
    reason: str = ""


def normalize_test_refs(
    record_id: str,
    value: object,
    *,
    workspace_root: Path,
) -> tuple[tuple[TestRef, ...], list[str]]:
    """Normalize the ``test_refs`` front-matter value for *record_id*.

    Returns ``(test_refs, warnings)``.  Path existence is validated against
    *workspace_root*; missing paths produce warnings (not errors) so that
    ``check`` can choose severity.
    """
    if value is None:
        return (), []
    if not isinstance(value, list):
        return (), [f"Record {record_id} test_refs must be a list."]

    refs: list[TestRef] = []
    warnings: list[str] = []
    for index, entry in enumerate(value, start=1):
        ref, entry_warnings = _normalize_test_ref_entry(
            record_id,
            entry,
            index=index,
            workspace_root=workspace_root,
        )
        warnings.extend(entry_warnings)
        if ref is not None:
            refs.append(ref)
    return tuple(refs), warnings


def _normalize_test_ref_entry(
    record_id: str,
    entry: object,
    *,
    index: int,
    workspace_root: Path,
) -> tuple[TestRef | None, list[str]]:
    warnings: list[str] = []

    # Compact string form: "path/to/test.py::test_func"
    if isinstance(entry, str):
        nodeid = entry.strip()
        if not nodeid:
            return None, [
                f"Record {record_id} test_refs entry {index} must be non-empty."
            ]
        path_text, _, nodeid_part = nodeid.partition("::")
        path_warnings = _validate_test_path(record_id, path_text, index, workspace_root)
        warnings.extend(path_warnings)
        return (
            TestRef(path=path_text.strip(), nodeid=nodeid_part.strip()),
            warnings,
        )

    if not isinstance(entry, dict):
        return (
            None,
            [
                f"Record {record_id} test_refs entry {index} must be a string "
                "or mapping."
            ],
        )

    raw_path = entry.get("path")
    raw_nodeid = entry.get("nodeid", "")
    raw_role = entry.get("role", "validates")
    raw_reason = entry.get("reason", "")

    if not isinstance(raw_path, str) or not raw_path.strip():
        return (
            None,
            [
                f"Record {record_id} test_refs entry {index} path must be a "
                "non-empty string."
            ],
        )
    path_text = raw_path.strip()

    if raw_nodeid and not isinstance(raw_nodeid, str):
        return (
            None,
            [f"Record {record_id} test_refs entry {index} nodeid must be a string."],
        )
    nodeid = raw_nodeid.strip() if isinstance(raw_nodeid, str) else ""

    if not isinstance(raw_role, str):
        return (
            None,
            [f"Record {record_id} test_refs entry {index} role must be a string."],
        )
    role = raw_role.strip() or "validates"

    if not isinstance(raw_reason, str):
        return (
            None,
            [f"Record {record_id} test_refs entry {index} reason must be a string."],
        )

    path_warnings = _validate_test_path(record_id, path_text, index, workspace_root)
    warnings.extend(path_warnings)

    return (
        TestRef(path=path_text, nodeid=nodeid, role=role, reason=raw_reason.strip()),
        warnings,
    )


def _validate_test_path(
    record_id: str,
    path_text: str,
    index: int,
    workspace_root: Path,
) -> list[str]:
    """Validate path format and existence; return warnings."""
    try:
        validate_relative_posix_path(
            path_text.split("::")[0].strip(),
            field_name=f"Record {record_id} test_refs entry {index} path",
        )
    except ValueError:
        return [
            f"Record {record_id} test_refs entry {index} "
            f"path must be a relative POSIX path: {path_text}"
        ]

    # Check file existence
    file_part = path_text.split("::")[0].strip()
    full_path = workspace_root / file_part
    if not full_path.exists():
        return [
            f"Record {record_id} test_refs entry {index} "
            f"path does not exist: {file_part}"
        ]
    return []


__all__ = ["TestRef", "normalize_test_refs"]
