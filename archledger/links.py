"""Generic record link normalization and validation.

Links describe directed relationships between records (e.g. satisfies,
depends_on, decided_by, mitigates). Target-existence validation is
handled by repository.check / sdd.check after all records are loaded,
not here.
"""

from __future__ import annotations

from dataclasses import dataclass

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
    }
)


@dataclass(frozen=True, slots=True)
class RecordLink:
    rel: str
    target: str
    reason: str = ""


def normalize_links(
    record_id: str,
    value: object,
) -> tuple[tuple[RecordLink, ...], list[str]]:
    """Normalize the ``links`` front-matter value for *record_id*.

    Returns ``(links, warnings)``.  Only shape/rel validation is done here;
    target-existence checks are handled by the caller after all records are
    loaded.
    """
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

    if not isinstance(raw_rel, str) or not raw_rel.strip():
        return (
            None,
            [f"Record {record_id} links entry {index} rel must be a non-empty string."],
        )
    rel = raw_rel.strip()
    if rel not in VALID_LINK_RELS:
        return (
            None,
            [
                f"Record {record_id} links entry {index} rel {rel!r} "
                "is not an allowed relationship. "
                f"Allowed: {', '.join(sorted(VALID_LINK_RELS))}"
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

    return RecordLink(rel=rel, target=target, reason=raw_reason.strip()), []


__all__ = [
    "VALID_LINK_RELS",
    "RecordLink",
    "normalize_links",
]
