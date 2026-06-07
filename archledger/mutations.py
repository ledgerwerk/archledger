"""Patch-safe mutation commands for archledger records.

Each helper reads front matter, mutates only the requested key or body,
updates ``updated_at``, and writes back.  The caller should re-validate
with ``repository.check()`` or targeted validation after mutation.
"""

from __future__ import annotations

from pathlib import Path

from archledger.errors import ValidationError
from archledger.links import VALID_LINK_RELS
from archledger.model import VALID_SOURCE_REF_ROLES
from archledger.storage.common import utc_now_iso
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)


def set_record_status(
    path: Path,
    record_id: str,
    status: str,
    *,
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    now = utc_now_iso()
    metadata = {**metadata, "status": status, "updated_at": now}
    write_front_matter_document(path, metadata, body)
    return metadata, body


def set_record_meta(
    path: Path,
    record_id: str,
    key: str,
    value: object,
    *,
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    now = utc_now_iso()
    metadata = {**metadata, key: value, "updated_at": now}
    write_front_matter_document(path, metadata, body)
    return metadata, body


def replace_record_body(
    path: Path,
    record_id: str,
    text: str,
    *,
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    """Replace the entire record body with *text*.

    Unlike :func:`append_record_body`, this removes the template placeholder
    body wholesale so accepted records do not trigger ``SDD-PLACEHOLDER``.
    """
    metadata, _body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    now = utc_now_iso()
    new_body = text.strip() + "\n"
    metadata = {**metadata, "updated_at": now}
    write_front_matter_document(path, metadata, new_body)
    return metadata, new_body


def append_record_body(
    path: Path,
    record_id: str,
    text: str,
    *,
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    now = utc_now_iso()
    new_body = body.rstrip() + "\n\n" + text.strip() + "\n"
    metadata = {**metadata, "updated_at": now}
    write_front_matter_document(path, metadata, new_body)
    return metadata, new_body


def add_source_ref(
    path: Path,
    record_id: str,
    ref_path: str,
    *,
    role: str = "",
    symbols: tuple[str, ...] = (),
    reason: str = "",
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    now = utc_now_iso()
    existing = metadata.get("source_refs", [])
    if not isinstance(existing, list):
        existing = []
    new_ref: dict[str, object] = {"path": ref_path}
    if symbols:
        new_ref["symbols"] = list(symbols)
    if role:
        if role not in VALID_SOURCE_REF_ROLES:
            raise ValidationError(f"Invalid source_ref role: {role!r}")
        new_ref["role"] = role
    if reason:
        new_ref["reason"] = reason
    existing.append(new_ref)
    metadata = {**metadata, "source_refs": existing, "updated_at": now}
    write_front_matter_document(path, metadata, body)
    return metadata, body


def add_link(
    path: Path,
    record_id: str,
    rel: str,
    target: str,
    *,
    reason: str = "",
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    if rel not in VALID_LINK_RELS:
        raise ValidationError(f"Invalid link rel: {rel!r}")
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    now = utc_now_iso()
    existing = metadata.get("links", [])
    if not isinstance(existing, list):
        existing = []
    new_link: dict[str, object] = {"rel": rel, "target": target}
    if reason:
        new_link["reason"] = reason
    existing.append(new_link)
    metadata = {**metadata, "links": existing, "updated_at": now}
    write_front_matter_document(path, metadata, body)
    return metadata, body


def add_acceptance_criterion(
    path: Path,
    record_id: str,
    statement: str,
    *,
    validation_command: str = "",
    expected: str = "passes",
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    now = utc_now_iso()
    existing = metadata.get("acceptance_criteria", [])
    if not isinstance(existing, list):
        existing = []
    new_ac: dict[str, object] = {
        "id": f"AC-{len(existing) + 1:03d}",
        "statement": statement,
    }
    if validation_command:
        new_ac["validation"] = {"command": validation_command, "expected": expected}
    existing.append(new_ac)
    metadata = {**metadata, "acceptance_criteria": existing, "updated_at": now}
    write_front_matter_document(path, metadata, body)
    return metadata, body


def _read_sdd_waivers(metadata: dict[str, object]) -> list[dict[str, object]]:
    raw_sdd = metadata.get("sdd")
    if not isinstance(raw_sdd, dict):
        return []
    raw_waivers = raw_sdd.get("waivers", [])
    if not isinstance(raw_waivers, list):
        return []
    return [w for w in raw_waivers if isinstance(w, dict)]


def add_sdd_waiver(
    path: Path,
    record_id: str,
    rule: str,
    reason: str,
    *,
    workspace_root: Path,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Append an ``sdd.waivers`` entry (deduped by rule).

    Requires a non-empty *reason* and a known *rule* code (validated by the
    caller against the rule registry).
    """
    if not reason or not reason.strip():
        raise ValidationError("SDD waiver requires a non-empty reason.")
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    existing = _read_sdd_waivers(metadata)
    if any(w.get("rule") == rule for w in existing):
        # Already waived; refresh the reason.
        existing = [
            {**w, "rule": rule, "reason": reason.strip()}
            if w.get("rule") == rule
            else w
            for w in existing
        ]
    else:
        existing.append({"rule": rule, "reason": reason.strip()})
    raw_sdd = metadata.get("sdd")
    if not isinstance(raw_sdd, dict):
        raw_sdd = {}
    raw_sdd = {**raw_sdd, "waivers": existing}
    now = utc_now_iso()
    metadata = {**metadata, "sdd": raw_sdd, "updated_at": now}
    write_front_matter_document(path, metadata, body)
    return metadata, existing


def list_sdd_waivers(
    path: Path,
    record_id: str,
    *,
    workspace_root: Path,
) -> list[dict[str, object]]:
    """Return the ``sdd.waivers`` entries for a record."""
    metadata, _body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    return _read_sdd_waivers(metadata)


def remove_sdd_waiver(
    path: Path,
    record_id: str,
    rule: str,
    *,
    workspace_root: Path,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Remove the ``sdd.waivers`` entry matching *rule* (if present)."""
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    existing = _read_sdd_waivers(metadata)
    remaining = [w for w in existing if w.get("rule") != rule]
    if len(remaining) == len(existing):
        return metadata, existing  # nothing to remove
    raw_sdd = metadata.get("sdd")
    if isinstance(raw_sdd, dict):
        raw_sdd = {**raw_sdd, "waivers": remaining}
    else:
        raw_sdd = {"waivers": remaining}
    now = utc_now_iso()
    metadata = {**metadata, "sdd": raw_sdd, "updated_at": now}
    write_front_matter_document(path, metadata, body)
    return metadata, remaining


def _assert_record_id(metadata: dict[str, object], expected_id: str) -> None:
    actual = metadata.get("id")
    if actual != expected_id:
        raise ValidationError(
            f"Record ID mismatch: expected {expected_id!r}, got {actual!r}"
        )


__all__ = [
    "add_acceptance_criterion",
    "add_link",
    "add_source_ref",
    "add_sdd_waiver",
    "append_record_body",
    "list_sdd_waivers",
    "remove_sdd_waiver",
    "replace_record_body",
    "set_record_meta",
    "set_record_status",
]
