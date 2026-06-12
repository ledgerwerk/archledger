"""Generic record link normalization and validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from ledgercore.errors import IdFormatError
from ledgercore.refs import parse_resource_ref

from archledger.source_refs import RelativePosixPathError, validate_relative_posix_path

RELATION_RE = re.compile(r"^[a-z][a-z0-9_:-]{0,63}$")
VALID_LINK_RELS: frozenset[str] = frozenset(
    {
        "satisfies",
        "depends_on",
        "decided_by",
        "constrained_by",
        "mitigates",
        "tested_by",
        "validates",
        "documents",
        "supersedes",
        "relates_to",
        "blocks",
        "applies_to",
        "implements",
    }
)
VALID_LINK_TARGET_KINDS: frozenset[str] = frozenset({"record", "path", "uri", "opaque"})
LEGACY_UNSEGMENTED_RE = re.compile(r"^[a-z][a-z0-9]*_\d+$")


@dataclass(frozen=True, slots=True)
class RecordLink:
    rel: str
    target: str
    reason: str = ""
    target_kind: str = "record"


def normalize_links(
    record_id: str,
    value: object,
) -> tuple[tuple[RecordLink, ...], list[str]]:
    """Normalize the ``links`` front-matter value for *record_id*."""
    if value is None:
        return (), []
    if not isinstance(value, list):
        return (), [f"Record {record_id} links must be a list."]

    links: list[RecordLink] = []
    warnings: list[str] = []
    for index, entry in enumerate(value, start=1):
        link, entry_warnings = _normalize_link_entry(record_id, entry, index=index)
        warnings.extend(entry_warnings)
        if link is not None:
            links.append(link)
    return tuple(links), warnings


def _normalize_link_entry(
    record_id: str,
    entry: object,
    *,
    index: int,
) -> tuple[RecordLink | None, list[str]]:
    if not isinstance(entry, dict):
        return (
            None,
            [f"Record {record_id} links entry {index} must be a mapping."],
        )

    raw_rel = entry.get("rel")
    raw_target = entry.get("target")
    raw_reason = entry.get("reason", "")
    raw_target_kind = entry.get("target_kind", "record")

    if not isinstance(raw_rel, str) or not raw_rel.strip():
        return (
            None,
            [f"Record {record_id} links entry {index} rel must be a non-empty string."],
        )
    rel = raw_rel.strip()
    if not RELATION_RE.fullmatch(rel):
        return (
            None,
            [
                f"Record {record_id} links entry {index} rel {rel!r} "
                "is not a valid relation token."
            ],
        )

    if not isinstance(raw_target_kind, str) or not raw_target_kind.strip():
        return (
            None,
            [
                f"Record {record_id} links entry {index} target_kind must be a "
                "non-empty string."
            ],
        )
    target_kind = raw_target_kind.strip()
    if target_kind not in VALID_LINK_TARGET_KINDS:
        return (
            None,
            [
                f"Record {record_id} links entry {index} target_kind "
                f"{target_kind!r} is not supported. "
                f"Allowed: {', '.join(sorted(VALID_LINK_TARGET_KINDS))}"
            ],
        )

    if not isinstance(raw_target, str) or not raw_target.strip():
        return (
            None,
            [
                f"Record {record_id} links entry {index} target must be a "
                "non-empty string."
            ],
        )
    target = raw_target.strip()

    if not isinstance(raw_reason, str):
        return (
            None,
            [f"Record {record_id} links entry {index} reason must be a string."],
        )

    target_warning = _validate_target(record_id, index, target_kind, target)
    if target_warning:
        return None, [target_warning]
    return (
        RecordLink(
            rel=rel,
            target=target,
            reason=raw_reason.strip(),
            target_kind=target_kind,
        ),
        [],
    )


def _validate_target(
    record_id: str,
    index: int,
    target_kind: str,
    target: str,
) -> str | None:
    if target_kind == "record":
        try:
            parse_resource_ref(target)
        except IdFormatError:
            if LEGACY_UNSEGMENTED_RE.fullmatch(target):
                return None
            return (
                f"Record {record_id} links entry {index} "
                "record target must be a valid reference."
            )
        return None
    if target_kind == "path":
        try:
            validate_relative_posix_path(
                target,
                field_name=f"Record {record_id} links entry {index} target",
            )
        except RelativePosixPathError as exc:
            return str(exc)
        return None
    if target_kind == "uri":
        parsed = urlparse(target)
        if not parsed.scheme:
            return (
                f"Record {record_id} links entry {index} uri target must include "
                "a URI scheme."
            )
        return None
    if target_kind == "opaque":
        return None
    return (
        f"Record {record_id} links entry {index} target_kind {target_kind!r} "
        "is not supported."
    )


__all__ = [
    "RELATION_RE",
    "VALID_LINK_RELS",
    "VALID_LINK_TARGET_KINDS",
    "RecordLink",
    "normalize_links",
]
