"""Ledger sequence helpers extracted from the repository.

Handles numbered-path scanning, gap detection, duplicate detection,
and counter floor logic. The repository delegates to these functions
to keep sequence validation testable in isolation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ledgercore.errors import IdFormatError
from ledgercore.refs import parse_local_ref

from archledger.storage.frontmatter import iter_source_files
from archledger.storage.meta import read_storage_meta
from archledger.storage.paths import ProjectPaths
from archledger.storage.project_config import ProjectConfig


@dataclass(frozen=True, slots=True)
class NumberedSourcePath:
    """A source file with a parsed ledger number."""

    number: int
    record_id: str
    path: Path
    storage_area: str


@dataclass(frozen=True, slots=True)
class SequenceFindings:
    """Results of ledger sequence analysis."""

    errors: tuple[tuple[str, str, Path | None], ...]  # (level, message, path)
    warnings: tuple[tuple[str, str, Path | None], ...]
    missing_numbers: tuple[int, ...]
    duplicate_numbers: tuple[int, ...]
    highest_seen: int


@dataclass(frozen=True, slots=True)
class SequenceInventory:
    """Authoritative numbered-file inventory used by checks and migration."""

    numbered_paths: tuple[NumberedSourcePath, ...]
    highest_seen: int
    stored_next_number: int
    derived_next_number: int
    missing_numbers: tuple[int, ...]
    duplicate_numbers: tuple[int, ...]


def inspect_sequence_inventory(
    paths: ProjectPaths,
    config: ProjectConfig,
    source_extensions: tuple[str, ...],
) -> SequenceInventory:
    numbered_paths = tuple(
        collect_numbered_source_paths(
            paths, config, source_extensions, include_archive=True
        )
    )
    meta = read_storage_meta(paths.storage_meta_path)
    by_number: dict[int, list[NumberedSourcePath]] = {}
    for item in numbered_paths:
        by_number.setdefault(item.number, []).append(item)
    highest_seen = max(by_number, default=0)
    upper_bound = max(highest_seen, meta.next_number - 1)
    missing_numbers = tuple(
        number for number in range(1, upper_bound + 1) if number not in by_number
    )
    duplicate_numbers = tuple(
        number for number, items in sorted(by_number.items()) if len(items) > 1
    )
    return SequenceInventory(
        numbered_paths=numbered_paths,
        highest_seen=highest_seen,
        stored_next_number=meta.next_number,
        derived_next_number=highest_seen + 1,
        missing_numbers=missing_numbers,
        duplicate_numbers=duplicate_numbers,
    )


def collect_numbered_source_paths(
    paths: ProjectPaths,
    config: ProjectConfig,
    source_extensions: tuple[str, ...],
    *,
    include_archive: bool,
) -> list[NumberedSourcePath]:
    """Scan workspace for numbered source files."""
    roots: list[tuple[str, Path]] = [
        ("section", paths.sections_dir),
        ("record", paths.records_dir),
    ]
    if include_archive:
        roots.append(("archive", paths.archive_dir))

    results: list[NumberedSourcePath] = []
    for storage_area, root in roots:
        for path in iter_source_files(root, source_extensions):
            try:
                number = parse_local_ref(path.stem, width=config.id_width).number
            except IdFormatError:
                continue
            results.append(
                NumberedSourcePath(
                    number=number,
                    record_id=path.stem,
                    path=path,
                    storage_area=storage_area,
                )
            )
    return results


def analyze_ledger_sequence(
    paths: ProjectPaths,
    config: ProjectConfig,
    source_extensions: tuple[str, ...],
    *,
    display_missing_id: Callable[[int], str],
) -> SequenceFindings:
    """Analyze ledger sequence for gaps, duplicates, and counter issues."""
    meta = read_storage_meta(paths.storage_meta_path)
    numbered_paths = collect_numbered_source_paths(
        paths, config, source_extensions, include_archive=True
    )

    by_number: dict[int, list[NumberedSourcePath]] = {}
    for item in numbered_paths:
        by_number.setdefault(item.number, []).append(item)

    highest_seen = max(by_number, default=0)
    upper_bound = max(highest_seen, meta.next_number - 1)
    missing_numbers = tuple(
        number for number in range(1, upper_bound + 1) if number not in by_number
    )
    duplicate_numbers = tuple(
        number for number, items in sorted(by_number.items()) if len(items) > 1
    )

    errors: list[tuple[str, str, Path | None]] = []
    warnings: list[tuple[str, str, Path | None]] = []

    for number in missing_numbers:
        errors.append(
            (
                "error",
                (
                    f"Missing ledger ID: {display_missing_id(number)}. "
                    "Move deleted items to archive or run: "
                    "archledger doctor --repair"
                ),
                None,
            )
        )
    for number in duplicate_numbers:
        locations = ", ".join(str(item.path) for item in by_number[number])
        errors.append(
            (
                "error",
                (
                    f"Duplicate ledger ID {display_missing_id(number)} "
                    f"appears in: {locations}"
                ),
                None,
            )
        )
    if meta.next_number <= highest_seen:
        warnings.append(
            (
                "warning",
                (
                    f"storage.yaml next_number is {meta.next_number}, "
                    f"but filesystem requires at least {highest_seen + 1}. "
                    "Run: archledger doctor --repair"
                ),
                paths.storage_meta_path,
            )
        )

    return SequenceFindings(
        errors=tuple(errors),
        warnings=tuple(warnings),
        missing_numbers=missing_numbers,
        duplicate_numbers=duplicate_numbers,
        highest_seen=highest_seen,
    )
