"""Detect whether a project uses legacy or current identity formats."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledgercore.errors import IdFormatError
from ledgercore.refs import parse_local_ref

from archledger.storage.frontmatter import iter_source_files, read_front_matter_document

LEGACY_SEGMENTED_RE = re.compile(r"^[a-z][a-z0-9]*_[a-z][a-z0-9_-]*_\d+$")


@dataclass(frozen=True, slots=True)
class IdentityFormatState:
    current_paths: tuple[Path, ...]
    legacy_paths: tuple[Path, ...]


def detect_identity_format_state(
    paths: ProjectPaths,  # noqa: F821
    config: ProjectConfig,  # noqa: F821
    source_extensions: tuple[str, ...],
) -> IdentityFormatState:
    """Scan project files and classify them as current or legacy identity."""
    current: list[Path] = []
    legacy: list[Path] = []
    for root in (paths.sections_dir, paths.records_dir, paths.archive_dir):
        for path in iter_source_files(root, source_extensions):
            try:
                metadata, _body = read_front_matter_document(path)
            except Exception:
                continue
            raw_id = str(metadata.get("id", path.stem)).strip()
            candidates = {path.stem, raw_id}
            if any(_is_local(candidate, config.id_width) for candidate in candidates):
                current.append(path)
                continue
            if any(_is_legacy_archledger_id(candidate) for candidate in candidates):
                legacy.append(path)
    return IdentityFormatState(tuple(current), tuple(legacy))


def _is_local(value: str, width: int) -> bool:
    try:
        parse_local_ref(value, width=width)
    except IdFormatError:
        return False
    return True


def _is_legacy_archledger_id(value: str) -> bool:
    return bool(
        LEGACY_UNSEGMENTED_RE.fullmatch(value) or LEGACY_SEGMENTED_RE.fullmatch(value)
    )


LEGACY_UNSEGMENTED_RE = re.compile(r"^[a-z][a-z0-9]*_\d+$")
