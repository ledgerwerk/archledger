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
    "append_record_body",
    "set_record_meta",
    "set_record_status",
]
