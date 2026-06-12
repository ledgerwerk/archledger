"""Compact agent context pack builder.

This module builds focused context packs for coding agents, selecting
only the records relevant to a file, record, topic, or set of changes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from archledger.model import ArchitectureRecord, record_sort_key
from archledger.repository import ArchitectureRepository
from archledger.scopes import scope_matches_path
from archledger.source_tracking import ChangeSet

# ---------------------------------------------------------------------------
# Topic query helpers
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+")
_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "for",
        "with",
        "is",
        "are",
        "on",
        "at",
        "by",
        "it",
        "that",
        "this",
        "as",
        "be",
        "from",
        "has",
        "have",
        "was",
        "will",
        "but",
        "not",
        "no",
        "all",
        "can",
        "do",
    }
)

CATEGORY_BY_TYPE: dict[str, str] = {
    "adr": "adrs",
    "constraint": "constraints",
    "glossary_term": "glossary_terms",
    "risk": "risks",
    "context_interface": "system_boundaries",
    "diagram": "architecture_docs",
    "white_box": "architecture_docs",
    "black_box": "architecture_docs",
    "interface": "system_boundaries",
    "concept": "architecture_docs",
    "strategy_item": "architecture_docs",
    "requirement": "architecture_docs",
    "quality_requirement": "architecture_docs",
    "quality_scenario": "architecture_docs",
    "runtime_scenario": "architecture_docs",
    "infrastructure": "architecture_docs",
    "section": "architecture_docs",
    "architecture_question": "unresolved_questions",
}

ALL_CATEGORIES = (
    "adrs",
    "constraints",
    "glossary_terms",
    "system_boundaries",
    "architecture_docs",
    "risks",
    "unresolved_questions",
)


def tokenize_query(topic: str) -> tuple[str, ...]:
    """Split *topic* into lowercase, non-stopword tokens."""
    raw = _TOKEN_RE.findall(topic)
    tokens: list[str] = []
    for part in raw:
        lowered = part.lower()
        # keep full token for exact match
        if lowered not in _STOPWORDS:
            tokens.append(lowered)
        # also split on internal delimiters for sub-tokens
        for sub in re.split(r"[_./:\\-]+", lowered):
            sub = sub.strip()
            if sub and sub not in _STOPWORDS and sub not in tokens:
                tokens.append(sub)
    return tuple(tokens)


@dataclass(frozen=True, slots=True)
class ScoredRecord:
    record: ArchitectureRecord
    score: float
    category: str
    match_reasons: tuple[str, ...]


def category_for_record(record: ArchitectureRecord) -> str:
    """Return the category name for *record*, defaulting to architecture_docs."""
    return CATEGORY_BY_TYPE.get(record.type, "architecture_docs")


def score_record(
    record: ArchitectureRecord,
    tokens: tuple[str, ...],
) -> tuple[float, tuple[str, ...]]:
    """Score *record* against *tokens*. Return (score, match_reasons)."""
    if not tokens or record.type == "section":
        return 0.0, ()

    score = 0.0
    reasons: list[str] = []

    # exact record id
    record_id_lower = record.id.lower()
    for t in tokens:
        if t == record_id_lower:
            score += 100
            reasons.append(f"exact record id: {record.id}")
            break

    # source_ref path matching
    for ref in record.source_refs:
        ref_lower = ref.path.lower().rstrip("/")
        for t in tokens:
            if t == ref_lower or ref_lower.startswith(t) or t in ref_lower.split("/"):
                score += 80
                reasons.append(f"source_ref matched path: {ref.path}")
                break

    # title token matching
    title_tokens = set(tokenize_query(record.title))
    for t in tokens:
        if t in title_tokens:
            score += 12
            reasons.append(f"title matched token: {t}")

    # glossary term exact match
    if record.type == "glossary_term":
        term = str(record.metadata.get("term", record.title)).lower()
        for t in tokens:
            if t == term:
                score += 35
                reasons.append(f"glossary term exact match: {t}")

    # metadata key/value token matching
    for key, value in record.metadata.items():
        if key in ("related",):
            continue
        val_str = str(value).lower() if value else ""
        for t in tokens:
            if t == val_str or (val_str and t in tokenize_query(val_str)):
                score += 8
                reasons.append(f"metadata matched {key}: {t}")
                break

    # body heading and token matching
    body_lower = record.body.lower()
    for line in body_lower.split("\n"):
        stripped = line.strip()
        if stripped.startswith("##") or stripped.startswith("=="):
            heading_tokens = set(tokenize_query(stripped.lstrip("#=").strip()))
            for t in tokens:
                if t in heading_tokens:
                    score += 10
                    reasons.append(f"body heading matched: {t}")
                    break
    # body token matching (capped)
    body_tokens = set(tokenize_query(body_lower))
    body_matches = 0
    for t in tokens:
        if t in body_tokens:
            body_matches += 1
    if body_matches:
        capped = min(body_matches * 2, 30)
        score += capped
        reasons.append(f"body matched {body_matches} token(s)")

    # section key/title matching
    section_lower = record.section.replace("_", " ").lower()
    for t in tokens:
        if t in section_lower.split():
            score += 10
            reasons.append(f"section matched: {record.section}")
            break

    # type/category matching
    cat = category_for_record(record)
    for t in tokens:
        if t in (record.type, cat.rstrip("s")):
            score += 6
            reasons.append(f"type matched: {record.type}")
            break

    # status bonus/penalty
    if record.status in ("accepted", "proposed"):
        score += 3
    elif record.status in ("deprecated", "superseded"):
        score -= 20

    return score, tuple(reasons)


def expand_linked_records(
    scored: list[ScoredRecord],
    records: list[ArchitectureRecord],
) -> list[ScoredRecord]:
    """Boost scores for records linked to/from high-scoring records."""
    high_ids = {sr.record.id for sr in scored if sr.score > 0}
    by_id = {r.id: r for r in records}
    boosted: list[ScoredRecord] = list(scored)
    scored_ids = {sr.record.id for sr in scored}

    for sr in scored:
        if sr.score <= 0:
            continue
        # outgoing links
        for link in sr.record.links:
            if link.target in scored_ids:
                # boost existing
                for i, b in enumerate(boosted):
                    if b.record.id == link.target:
                        boosted[i] = ScoredRecord(
                            record=b.record,
                            score=b.score + 15,
                            category=b.category,
                            match_reasons=b.match_reasons
                            + (f"linked from {sr.record.id}",),
                        )
            elif link.target in by_id:
                target_rec = by_id[link.target]
                if target_rec.type != "section":
                    boosted.append(
                        ScoredRecord(
                            record=target_rec,
                            score=15,
                            category=category_for_record(target_rec),
                            match_reasons=(f"linked from {sr.record.id}",),
                        )
                    )
                    scored_ids.add(target_rec.id)
        # incoming links
        for r in records:
            if r.id in scored_ids or r.type == "section":
                continue
            for link in r.links:
                if link.target == sr.record.id:
                    boosted.append(
                        ScoredRecord(
                            record=r,
                            score=10,
                            category=category_for_record(r),
                            match_reasons=(f"incoming link to {sr.record.id}",),
                        )
                    )
                    scored_ids.add(r.id)
                    break

    return boosted


def group_by_category(
    scored: list[ScoredRecord],
    max_per_category: int,
    workspace_root: Path,
    include_body: bool,
) -> dict[str, list[dict[str, Any]]]:
    """Group scored records by category and serialize."""
    buckets: dict[str, list[ScoredRecord]] = {cat: [] for cat in ALL_CATEGORIES}
    for sr in scored:
        if sr.score <= 0:
            continue
        buckets.setdefault(sr.category, []).append(sr)

    categories: dict[str, list[dict[str, Any]]] = {}
    for cat in ALL_CATEGORIES:
        items = sorted(buckets.get(cat, []), key=lambda s: s.score, reverse=True)
        items = items[:max_per_category]
        entries: list[dict[str, Any]] = []
        for sr in items:
            rec_dict = _serialize_single_record(sr.record, workspace_root, include_body)
            entries.append(
                {
                    "id": sr.record.id,
                    "score": sr.score,
                    "match_reasons": list(sr.match_reasons),
                    "record": rec_dict,
                }
            )
        categories[cat] = entries
    return categories


def _serialize_single_record(
    r: ArchitectureRecord,
    workspace_root: Path,
    include_body: bool,
) -> dict[str, Any]:
    path_str = str(r.path)
    try:
        path_str = str(r.path.relative_to(workspace_root))
    except ValueError:
        pass
    item: dict[str, Any] = {
        "id": r.id,
        "type": r.type,
        "title": r.title,
        "status": r.status,
        "section": r.section,
        "order": r.order,
        "path": path_str,
    }
    if r.source_refs:
        item["source_refs"] = [
            {"path": ref.path, "symbols": list(ref.symbols), "role": ref.role}
            for ref in r.source_refs
        ]
    if r.links:
        item["links"] = [{"rel": link.rel, "target": link.target} for link in r.links]
    if r.test_refs:
        item["test_refs"] = [
            {"path": tr.path, "nodeid": tr.nodeid, "role": tr.role}
            for tr in r.test_refs
        ]
    if include_body:
        item["body"] = r.body
    return item


def build_context_for_file(
    repo: ArchitectureRepository,
    file_path: str,
    *,
    include_body: bool = False,
    max_records: int = 20,
) -> dict[str, Any]:
    """Build a context pack focused on *file_path*.

    Selection rules:
    1. Include records whose source_refs match the file.
    2. Include records linked to those records.
    3. Include ADRs linked via links, related, or source refs.
    4. Include requirements and acceptance criteria connected to the file.
    5. Include open risks connected to the file or record set.
    6. Sort by record_sort_key and cap by max_records.
    """
    records = repo.load_all_records(include_sections=True)
    workspace_root = repo.paths.workspace_root

    # Step 1: records whose source_refs match the file
    matched: set[str] = set()
    file_path_normalized = file_path.replace("\\", "/").strip()
    for r in records:
        for ref in r.source_refs:
            ref_path = ref.path.rstrip("/")
            if ref_path == file_path_normalized or file_path_normalized.startswith(
                ref_path
            ):
                matched.add(r.id)
                break

    # Step 1b: records whose scope matches the file
    for r in records:
        if r.id not in matched and r.scope is not None:
            if scope_matches_path(r.scope, file_path_normalized):
                matched.add(r.id)

    # Step 2: records linked to matched records
    linked: set[str] = set()
    for r in records:
        if r.id in matched:
            for link in r.links:
                linked.add(link.target)
            # Also check related
            related = r.metadata.get("related")
            if isinstance(related, list):
                linked.update(str(item) for item in related if item)

    # Step 3: records that link TO matched records
    incoming: set[str] = set()
    for r in records:
        for link in r.links:
            if link.target in matched:
                incoming.add(r.id)

    # Collect all relevant IDs
    relevant_ids = matched | linked | incoming
    relevant = [r for r in records if r.id in relevant_ids and r.type != "section"]
    relevant.sort(key=record_sort_key)
    relevant = relevant[:max_records]

    return _build_payload(
        records=relevant,
        workspace_root=workspace_root,
        include_body=include_body,
        query={
            "for_file": file_path,
            "for_record": None,
            "changed": False,
            "max_records": max_records,
            "include_body": include_body,
        },
    )


def build_context_for_record(
    repo: ArchitectureRepository,
    record_id: str,
    *,
    include_body: bool = False,
    max_records: int = 20,
) -> dict[str, Any]:
    """Build a context pack focused on *record_id*."""
    records = repo.load_all_records(include_sections=True)
    workspace_root = repo.paths.workspace_root

    by_id = {r.id: r for r in records}
    root = by_id.get(record_id)
    if root is None:
        return _empty_payload(
            query={
                "for_file": None,
                "for_record": record_id,
                "changed": False,
                "max_records": max_records,
                "include_body": include_body,
            }
        )

    relevant_ids: set[str] = {record_id}
    # Links out
    for link in root.links:
        relevant_ids.add(link.target)
    # Links in
    for r in records:
        for link in r.links:
            if link.target == record_id:
                relevant_ids.add(r.id)
    # Related
    related = root.metadata.get("related")
    if isinstance(related, list):
        relevant_ids.update(str(item) for item in related if item)

    relevant = [r for r in records if r.id in relevant_ids and r.type != "section"]
    relevant.sort(key=record_sort_key)
    relevant = relevant[:max_records]

    return _build_payload(
        records=relevant,
        workspace_root=workspace_root,
        include_body=include_body,
        query={
            "for_file": None,
            "for_record": record_id,
            "changed": False,
            "max_records": max_records,
            "include_body": include_body,
        },
    )


def build_context_for_changed(
    repo: ArchitectureRepository,
    changes: ChangeSet,
    *,
    include_body: bool = False,
    max_records: int = 20,
) -> dict[str, Any]:
    """Build a context pack focused on the changed files in *changes*."""
    records = repo.load_all_records(include_sections=True)
    workspace_root = repo.paths.workspace_root

    # impacted record IDs
    impacted_ids = {imp.id for imp in changes.impacted_records}
    # Also collect related records
    related_ids: set[str] = set()
    for r in records:
        if r.id in impacted_ids:
            for link in r.links:
                related_ids.add(link.target)
    all_ids = impacted_ids | related_ids

    relevant = [r for r in records if r.id in all_ids and r.type != "section"]
    relevant.sort(key=record_sort_key)
    relevant = relevant[:max_records]

    return _build_payload(
        records=relevant,
        workspace_root=workspace_root,
        include_body=include_body,
        query={
            "for_file": None,
            "for_record": None,
            "changed": True,
            "max_records": max_records,
            "include_body": include_body,
        },
    )


def build_context_for_topic(
    repo: ArchitectureRepository,
    topic: str,
    *,
    include_body: bool = False,
    include_draft: bool = False,
    include_superseded: bool = False,
    max_records: int = 40,
    max_per_category: int = 8,
    scope: str | None = None,
    scope_kind: str | None = None,
    addon: str | None = None,
) -> dict[str, Any]:
    """Build a categorized context pack for *topic* with scoring."""
    from archledger.scopes import VALID_SCOPE_KINDS

    tokens = tokenize_query(topic)
    if not tokens:
        return _empty_topic_payload(
            topic=topic,
            include_body=include_body,
            max_records=max_records,
            max_per_category=max_per_category,
            include_draft=include_draft,
            include_superseded=include_superseded,
            scope=scope,
            scope_kind=scope_kind,
            addon=addon,
            warnings=["Topic produced no searchable tokens."],
        )

    records = repo.load_all_records(include_sections=True)
    workspace_root = repo.paths.workspace_root

    # Score all records
    scored: list[ScoredRecord] = []
    for r in records:
        # status filtering
        if r.status == "draft" and not include_draft:
            continue
        if r.status == "superseded" and not include_superseded:
            continue
        # scope/addon filtering (mirrors repository.list_records)
        if scope is not None or scope_kind is not None or addon is not None:
            if r.scope is None:
                continue
            if scope is not None and r.scope.name != scope:
                continue
            if scope_kind is not None and scope_kind not in VALID_SCOPE_KINDS:
                continue
            if scope_kind is not None and r.scope.kind != scope_kind:
                continue
            if addon is not None:
                addon_dir = addon if addon.endswith("/") else addon + "/"
                if not any(
                    addon_dir == apply_to
                    or addon_dir.startswith(apply_to.rstrip("/") + "/")
                    or apply_to.rstrip("/") == addon
                    for apply_to in r.scope.applies_to
                ):
                    continue
        s, reasons = score_record(r, tokens)
        s, reasons = score_record(r, tokens)
        if s > 0:
            scored.append(
                ScoredRecord(
                    record=r,
                    score=s,
                    category=category_for_record(r),
                    match_reasons=reasons,
                )
            )

    # Expand linked records
    scored = expand_linked_records(scored, records)

    # Deduplicate
    seen: set[str] = set()
    unique: list[ScoredRecord] = []
    for sr in scored:
        if sr.record.id not in seen:
            seen.add(sr.record.id)
            unique.append(sr)

    # Sort by score descending, then by sort key for ties
    unique.sort(key=lambda sr: (-sr.score, record_sort_key(sr.record)))

    # Group by category
    categories = group_by_category(
        unique, max_per_category, workspace_root, include_body
    )

    # Build flat records list (deduplicated, capped)
    flat_records = [sr.record for sr in unique[:max_records]]
    flat_serialized = _serialize_records(flat_records, workspace_root, include_body)

    # Summary
    categories_returned = [cat for cat, items in categories.items() if items]
    total_returned = sum(len(items) for items in categories.values())

    warnings: list[str] = []
    # warn if architecture_question type is missing
    has_aq = any(r.type == "architecture_question" for r in records)
    if not has_aq:
        warnings.append(
            "Unresolved architecture questions are not first-class records in this project."
        )

    return {
        "schema": "archledger.context.v2",
        "query": {
            "topic": topic,
            "for_file": None,
            "for_record": None,
            "changed": False,
            "include_body": include_body,
            "max_records": max_records,
            "max_per_category": max_per_category,
            "include_drafts": include_draft,
            "include_superseded": include_superseded,
            "scope": scope,
            "scope_kind": scope_kind,
            "addon": addon,
        },
        "summary": {
            "records_considered": len(records),
            "records_returned": total_returned,
            "categories_returned": categories_returned,
        },
        "categories": categories,
        "records": flat_serialized,
        "warnings": warnings,
    }


def _build_payload(
    *,
    records: list[ArchitectureRecord],
    workspace_root: Path,
    include_body: bool,
    query: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {"schema": "archledger.context.v1", "query": query}
    result["records"] = _serialize_records(records, workspace_root, include_body)
    return result


def _serialize_records(
    records: list[ArchitectureRecord],
    workspace_root: Path,
    include_body: bool,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for r in records:
        path_str = str(r.path)
        try:
            path_str = str(r.path.relative_to(workspace_root))
        except ValueError:
            pass
        item: dict[str, Any] = {
            "id": r.id,
            "type": r.type,
            "title": r.title,
            "status": r.status,
            "section": r.section,
            "order": r.order,
            "path": path_str,
        }
        if r.source_refs:
            item["source_refs"] = [
                {"path": ref.path, "symbols": list(ref.symbols), "role": ref.role}
                for ref in r.source_refs
            ]
        if r.links:
            item["links"] = [
                {"rel": link.rel, "target": link.target} for link in r.links
            ]
        if r.test_refs:
            item["test_refs"] = [
                {"path": tr.path, "nodeid": tr.nodeid, "role": tr.role}
                for tr in r.test_refs
            ]
        if include_body:
            item["body"] = r.body
        items.append(item)
    return items


def _empty_topic_payload(
    *,
    topic: str,
    include_body: bool,
    max_records: int,
    max_per_category: int,
    include_draft: bool,
    include_superseded: bool,
    scope: str | None,
    scope_kind: str | None,
    addon: str | None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema": "archledger.context.v2",
        "query": {
            "topic": topic,
            "for_file": None,
            "for_record": None,
            "changed": False,
            "include_body": include_body,
            "max_records": max_records,
            "max_per_category": max_per_category,
            "include_drafts": include_draft,
            "include_superseded": include_superseded,
            "scope": scope,
            "scope_kind": scope_kind,
            "addon": addon,
        },
        "summary": {
            "records_considered": 0,
            "records_returned": 0,
            "categories_returned": [],
        },
        "categories": {cat: [] for cat in ALL_CATEGORIES},
        "records": [],
        "warnings": warnings or [],
    }


__all__ = [
    "ALL_CATEGORIES",
    "CATEGORY_BY_TYPE",
    "ScoredRecord",
    "build_context_for_changed",
    "build_context_for_file",
    "build_context_for_record",
    "build_context_for_topic",
    "category_for_record",
    "expand_linked_records",
    "group_by_category",
    "score_record",
    "tokenize_query",
]
