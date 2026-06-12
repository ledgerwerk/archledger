from __future__ import annotations

from pathlib import Path

from ledgercore.errors import FrontMatterError as CoreFrontMatterError
from ledgercore.frontmatter import (
    read_front_matter_document as _read_front_matter_document,
)
from ledgercore.frontmatter import (
    write_front_matter_document as _write_front_matter_document,
)
from ledgercore.io import normalize_newlines

from archledger.errors import FrontMatterError


def normalize_front_matter_newlines(text: str) -> str:
    return normalize_newlines(text)


def read_front_matter_document(path: Path) -> tuple[dict[str, object], str]:
    try:
        return _read_front_matter_document(path)
    except CoreFrontMatterError as exc:
        raise FrontMatterError(str(exc)) from exc


def write_front_matter_document(
    path: Path,
    metadata: dict[str, object],
    body: str,
) -> None:
    try:
        normalized_body = normalize_newlines(body)
        if normalized_body and not normalized_body.endswith("\n"):
            normalized_body = normalized_body + "\n"
        _write_front_matter_document(path, metadata, normalized_body)
    except CoreFrontMatterError as exc:
        raise FrontMatterError(str(exc)) from exc


def read_markdown_front_matter(path: Path) -> tuple[dict[str, object], str]:
    return read_front_matter_document(path)


def write_markdown_front_matter(
    path: Path,
    metadata: dict[str, object],
    body: str,
) -> None:
    write_front_matter_document(path, metadata, body)


def iter_source_files(directory: Path, extensions: tuple[str, ...]) -> list[Path]:
    if not directory.exists():
        return []
    normalized_extensions = {extension.lower() for extension in extensions}
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in normalized_extensions
    )
