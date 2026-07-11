"""Patch-safe mutation commands for archledger records.

Each helper reads front matter, mutates only the requested key or body,
increments ``version``, and writes back.  The caller should re-validate
with ``repository.check()`` or targeted validation after mutation.
"""

from __future__ import annotations

from pathlib import Path

from archledger.errors import ValidationError
from archledger.links import RELATION_RE
from archledger.metadata_version import bump_metadata_version, metadata_version
from archledger.model import VALID_SOURCE_REF_ROLES
from archledger.source_refs import RelativePosixPathError, validate_relative_posix_path
from archledger.storage.frontmatter import (
    read_front_matter_document,
    split_front_matter_text,
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
    metadata = bump_metadata_version({**metadata, "status": status})
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
    metadata = bump_metadata_version({**metadata, key: value})
    write_front_matter_document(path, metadata, body)
    return metadata, body


def export_record_document(path: Path, record_id: str) -> str:
    metadata, _body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    return path.read_text(encoding="utf-8")


def apply_record_document(
    path: Path,
    record_id: str,
    document_text: str,
    *,
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    del workspace_root
    current_metadata, current_body = read_front_matter_document(path)
    _assert_record_id(current_metadata, record_id)
    candidate_metadata, candidate_body = split_front_matter_text(document_text)
    _assert_record_id(candidate_metadata, record_id)
    if candidate_metadata.get("kind") != current_metadata.get("kind"):
        raise ValidationError(
            f"Record kind mismatch: expected {current_metadata.get('kind')!r}, "
            f"got {candidate_metadata.get('kind')!r}"
        )

    candidate_metadata = {
        **candidate_metadata,
        "version": current_metadata.get("version"),
    }
    if candidate_metadata == current_metadata and candidate_body == current_body:
        return current_metadata, current_body

    updated_metadata = {
        **candidate_metadata,
        "version": metadata_version(current_metadata) + 1,
    }
    write_front_matter_document(path, updated_metadata, candidate_body)
    return updated_metadata, candidate_body


def replace_record_body(
    path: Path,
    record_id: str,
    text: str,
    *,
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    """Replace the entire record body with *text*.

    Unlike :func:`append_record_body`, this removes the template placeholder
    body wholesale so normal content checks do not report placeholder text.
    """
    metadata, _body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    new_body = text.strip() + "\n"
    metadata = bump_metadata_version(metadata)
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
    new_body = body.rstrip() + "\n\n" + text.strip() + "\n"
    metadata = bump_metadata_version(metadata)
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
    metadata = bump_metadata_version({**metadata, "source_refs": existing})
    write_front_matter_document(path, metadata, body)
    return metadata, body


def add_test_ref(
    path: Path,
    record_id: str,
    ref_path: str,
    *,
    nodeid: str = "",
    role: str = "validates",
    reason: str = "",
    workspace_root: Path,
) -> tuple[dict[str, object], str]:
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    existing = metadata.get("test_refs", [])
    if not isinstance(existing, list):
        existing = []
    try:
        normalized_ref_path = validate_relative_posix_path(
            ref_path,
            field_name=f"Record {record_id} test_refs path",
        )
    except RelativePosixPathError as exc:
        raise ValidationError(str(exc)) from exc
    new_ref: dict[str, object] = {"path": normalized_ref_path}
    if nodeid:
        new_ref["nodeid"] = nodeid
    if role:
        new_ref["role"] = role
    if reason:
        new_ref["reason"] = reason
    existing.append(new_ref)
    metadata = bump_metadata_version({**metadata, "test_refs": existing})
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
    if not RELATION_RE.fullmatch(rel):
        raise ValidationError(f"Invalid link rel: {rel!r}")
    metadata, body = read_front_matter_document(path)
    _assert_record_id(metadata, record_id)
    existing = metadata.get("links", [])
    if not isinstance(existing, list):
        existing = []
    new_link: dict[str, object] = {"rel": rel, "target": target}
    if reason:
        new_link["reason"] = reason
    existing.append(new_link)
    metadata = bump_metadata_version({**metadata, "links": existing})
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
    metadata = bump_metadata_version({**metadata, "acceptance_criteria": existing})
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
    "add_test_ref",
    "apply_record_document",
    "append_record_body",
    "export_record_document",
    "replace_record_body",
    "set_record_meta",
    "set_record_status",
]
