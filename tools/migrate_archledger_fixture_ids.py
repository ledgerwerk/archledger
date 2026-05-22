from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from archledger.model import (
    ArchitectureRecord,
    MAJOR_SECTION_SPECS,
    record_sort_key,
)
from archledger.storage.frontmatter import read_front_matter_document

ROOT = Path(__file__).resolve().parents[1]
ARCHLEDGER_DIR = ROOT / ".archledger"
SECTIONS_DIR = ARCHLEDGER_DIR / "sections"
RECORDS_DIR = ARCHLEDGER_DIR / "records"
STORAGE_PATH = ARCHLEDGER_DIR / "storage.yaml"


@dataclass(slots=True)
class FileDoc:
    path: Path
    metadata: dict[str, Any]
    body: str


def _render_frontmatter(metadata: dict[str, Any], body: str) -> str:
    import yaml

    front = yaml.safe_dump(metadata, sort_keys=False).rstrip()
    return f"---\n{front}\n---\n\n{body.rstrip()}\n"


def _replace_refs(value: Any, id_map: dict[str, str]) -> Any:
    if isinstance(value, str):
        return id_map.get(value, value)
    if isinstance(value, list):
        return [_replace_refs(item, id_map) for item in value]
    if isinstance(value, dict):
        return {key: _replace_refs(item, id_map) for key, item in value.items()}
    return value


def main() -> None:
    section_docs: list[FileDoc] = []
    section_map: dict[str, str] = {}
    for spec in MAJOR_SECTION_SPECS:
        old_path = SECTIONS_DIR / f"{spec.order // 10:02d}_{spec.key}.md"
        metadata, body = read_front_matter_document(old_path)
        old_id = str(metadata["id"])
        new_id = f"al_{spec.number:04d}"
        section_map[old_id] = new_id
        section_docs.append(FileDoc(path=old_path, metadata=metadata, body=body))

    record_docs: list[FileDoc] = []
    for path in sorted(RECORDS_DIR.rglob("*.md")):
        metadata, body = read_front_matter_document(path)
        record_docs.append(FileDoc(path=path, metadata=metadata, body=body))

    sortable: list[tuple[ArchitectureRecord, FileDoc]] = []
    for doc in record_docs:
        metadata = doc.metadata
        record = ArchitectureRecord(
            id=str(metadata["id"]),
            type=str(metadata["type"]),
            title=str(metadata["title"]),
            status=str(metadata["status"]),
            section=str(metadata["section"]),
            order=int(metadata["order"]),
            path=doc.path,
            metadata=metadata,
            body=doc.body,
            source_refs=(),
        )
        sortable.append((record, doc))

    sortable.sort(key=lambda item: record_sort_key(item[0]))

    record_map: dict[str, str] = {}
    next_number = 13
    for record, _doc in sortable:
        record_map[record.id] = f"al_{next_number:04d}"
        next_number += 1

    id_map = {**section_map, **record_map}

    output: dict[Path, str] = {}

    for doc in section_docs + [doc for _, doc in sortable]:
        old_id = str(doc.metadata["id"])
        new_id = id_map[old_id]
        new_metadata = _replace_refs(doc.metadata, id_map)
        new_metadata["id"] = new_id
        new_body = doc.body
        for old, new in id_map.items():
            new_body = new_body.replace(old, new)
        new_text = _render_frontmatter(new_metadata, new_body)
        new_path = doc.path.with_name(f"{new_id}{doc.path.suffix}")
        output[new_path] = new_text

    # Remove old markdown files
    for path in list(SECTIONS_DIR.glob("*.md")) + list(RECORDS_DIR.rglob("*.md")):
        path.unlink()

    # Write migrated files
    for path, text in output.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    STORAGE_PATH.write_text(
        "\n".join(
            [
                "storage_version: 2",
                "created_with_archledger: 0.1.dev2+gfebe6dc46.d19800101",
                "project_uuid: 6bddbb56-b273-4aae-9860-bfa4de93f115",
                'created_at: "2026-05-19T18:50:37Z"',
                f"next_number: {next_number}",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
