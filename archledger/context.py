"""Compact agent context pack builder.

This module builds focused context packs for coding agents, selecting
only the records relevant to a file, record, or set of changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from archledger.model import ArchitectureRecord, record_sort_key
from archledger.repository import ArchitectureRepository
from archledger.source_tracking import ChangeSet


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


def _empty_payload(query: dict[str, Any]) -> dict[str, Any]:
    return {"schema": "archledger.context.v1", "query": query, "records": []}


__all__ = [
    "build_context_for_changed",
    "build_context_for_file",
    "build_context_for_record",
]
