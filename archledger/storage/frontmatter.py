from __future__ import annotations

from pathlib import Path

import yaml

from archledger.errors import FrontMatterError
from archledger.storage.common import normalize_newlines, read_text, write_text


def normalize_front_matter_newlines(text: str) -> str:
    return normalize_newlines(text)


def read_markdown_front_matter(path: Path) -> tuple[dict[str, object], str]:
    text = normalize_front_matter_newlines(read_text(path))
    if not text.startswith("---\n"):
        raise FrontMatterError(f"Markdown file has no YAML front matter: {path}")

    end = text.find("\n---\n", 4)
    if end == -1:
        if text.endswith("\n---"):
            yaml_text = text[4:-4]
            body = ""
        else:
            raise FrontMatterError(
                f"Markdown file has no closing YAML delimiter: {path}"
            )
    else:
        yaml_text = text[4:end]
        body = text[end + len("\n---\n") :]

    try:
        metadata = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise FrontMatterError(f"Invalid YAML front matter in {path}") from exc

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise FrontMatterError(f"YAML front matter is not a mapping in {path}")

    return dict(metadata), body


def write_markdown_front_matter(
    path: Path,
    metadata: dict[str, object],
    body: str,
) -> None:
    yaml_text = yaml.safe_dump(metadata, sort_keys=False)
    document = f"---\n{yaml_text}---\n"
    normalized_body = normalize_front_matter_newlines(body)
    if normalized_body:
        document = f"{document}{normalized_body.rstrip()}\n"
    write_text(path, document)


def iter_markdown_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.rglob("*.md") if path.is_file())
