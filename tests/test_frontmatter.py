from __future__ import annotations

from pathlib import Path

import pytest

from archledger.errors import FrontMatterError
from archledger.storage.frontmatter import (
    read_markdown_front_matter,
    write_markdown_front_matter,
)


def test_read_markdown_front_matter_valid_document(tmp_path: Path) -> None:
    path = tmp_path / "record.md"
    path.write_text("---\nid: demo\norder: 10\n---\nbody\n", encoding="utf-8")

    metadata, body = read_markdown_front_matter(path)

    assert metadata == {"id": "demo", "order": 10}
    assert body == "body\n"


def test_read_markdown_front_matter_rejects_missing_frontmatter(tmp_path: Path) -> None:
    path = tmp_path / "record.md"
    path.write_text("body only\n", encoding="utf-8")

    with pytest.raises(FrontMatterError):
        read_markdown_front_matter(path)


def test_read_markdown_front_matter_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    path = tmp_path / "record.md"
    path.write_text("---\n- invalid\n---\nbody\n", encoding="utf-8")

    with pytest.raises(FrontMatterError):
        read_markdown_front_matter(path)


def test_write_markdown_front_matter_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "record.md"
    write_markdown_front_matter(path, {"id": "demo", "order": 10}, "body")

    metadata, body = read_markdown_front_matter(path)

    assert metadata == {"id": "demo", "order": 10}
    assert body == "body\n"
