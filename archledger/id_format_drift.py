from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archledger.ids import LedgerIdFormat
from archledger.storage.frontmatter import iter_source_files, read_front_matter_document
from archledger.storage.paths import ProjectPaths
from archledger.storage.project_config import ProjectConfig


@dataclass(frozen=True, slots=True)
class IdFormatDrift:
    path: Path
    record_id: str
    detected_format: LedgerIdFormat
    configured_format: LedgerIdFormat


def alternate_segment_format(config: ProjectConfig) -> LedgerIdFormat:
    alt_mode = "none" if config.id_segment_mode == "type" else "type"
    return LedgerIdFormat(
        prefix=config.id_prefix,
        width=config.id_width,
        segment_mode=alt_mode,
    )


def find_id_format_drift(
    paths: ProjectPaths,
    config: ProjectConfig,
    source_extensions: tuple[str, ...],
) -> tuple[IdFormatDrift, ...]:
    configured = config.id_format
    alternate = alternate_segment_format(config)
    roots = (paths.sections_dir, paths.records_dir, paths.archive_dir)
    findings: list[IdFormatDrift] = []

    for root in roots:
        for path in iter_source_files(root, source_extensions):
            stem = path.stem
            if configured.is_id(stem):
                continue
            if not alternate.is_id(stem):
                continue
            try:
                metadata, _ = read_front_matter_document(path)
            except Exception:
                # Let normal frontmatter validation report this.
                continue
            record_id = str(metadata.get("id") or stem)
            findings.append(
                IdFormatDrift(
                    path=path,
                    record_id=record_id,
                    detected_format=alternate,
                    configured_format=configured,
                )
            )
    return tuple(findings)
