from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

from ledgercore.errors import JsonStoreError
from ledgercore.jsonio import load_json_object, write_json

from archledger.errors import RenderError
from archledger.metadata_version import require_version
from archledger.model import ArchitectureRecord

DOCUMENT_STATE_SCHEMA = "archledger.document-state.v1"


def build_document_state_key(
    *,
    profile: str,
    source_format: str,
    include_draft: bool,
    include_superseded: bool,
) -> str:
    return (
        f"{profile}:{source_format}:draft={str(include_draft).lower()}:"
        f"superseded={str(include_superseded).lower()}"
    )


def build_document_fingerprint(
    *,
    title: str,
    arc42_template_version: str,
    source_format: str,
    include_draft: bool,
    include_superseded: bool,
    records: Iterable[ArchitectureRecord],
    sections: Iterable[ArchitectureRecord],
) -> str:
    def record_input(record: ArchitectureRecord) -> dict[str, object]:
        try:
            version = require_version(record.metadata.get("version"))
        except ValueError as exc:
            raise RenderError(f"Record {record.id} has an invalid version.") from exc
        return {
            "id": record.id,
            "type": record.type,
            "section": record.section,
            "order": record.order,
            "status": record.status,
            "version": version,
        }

    payload = {
        "profile": "arc42",
        "title": title,
        "arc42_template_version": arc42_template_version,
        "source_format": source_format,
        "include_draft": include_draft,
        "include_superseded": include_superseded,
        "records": [record_input(item) for item in sorted(records, key=lambda x: x.id)],
        "sections": [
            record_input(item) for item in sorted(sections, key=lambda x: x.id)
        ],
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def resolve_document_version(
    state_path: Path,
    *,
    logical_key: str,
    fingerprint: str,
    input_count: int,
    write: bool,
) -> int:
    state = _read_state(state_path)
    documents = state["documents"]
    assert isinstance(documents, dict)
    existing = documents.get(logical_key)
    if existing is None:
        version = 1
    else:
        if not isinstance(existing, dict):
            raise RenderError("document-state document entry must be an object.")
        try:
            stored_version = require_version(existing.get("version"))
        except ValueError as exc:
            raise RenderError(
                "document-state document version must be a positive integer."
            ) from exc
        stored_fingerprint = existing.get("fingerprint")
        if not isinstance(stored_fingerprint, str) or not stored_fingerprint:
            raise RenderError("document-state fingerprint must be a non-empty string.")
        version = (
            stored_version if stored_fingerprint == fingerprint else stored_version + 1
        )
    if write and (
        existing is None
        or existing.get("fingerprint") != fingerprint
        or existing.get("input_count") != input_count
    ):
        documents[logical_key] = {
            "version": version,
            "fingerprint": fingerprint,
            "input_count": input_count,
        }
        write_json(state_path, state)
    return version


def _read_state(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"schema": DOCUMENT_STATE_SCHEMA, "documents": {}}
    try:
        data = load_json_object(path, label="document-state JSON")
    except JsonStoreError as exc:
        raise RenderError(f"Invalid document-state JSON in {path}.") from exc
    if data.get("schema") != DOCUMENT_STATE_SCHEMA:
        raise RenderError("Unsupported document-state schema.")
    documents = data.get("documents")
    if not isinstance(documents, dict):
        raise RenderError("document-state documents must be an object.")
    return data
