from __future__ import annotations

from collections.abc import Mapping

from ledgercore.refs import normalize_kind

from archledger.model import ArchitectureRecord
from archledger.storage.project_config import ProjectConfig


def identity_kind_for_metadata(
    metadata: Mapping[str, object],
    *,
    default_kind: str,
    kind_map: Mapping[str, str],
) -> str:
    explicit = metadata.get("kind")
    if isinstance(explicit, str) and explicit.strip():
        return normalize_kind(explicit)

    record_type = metadata.get("type")
    if isinstance(record_type, str):
        mapped = kind_map.get(record_type)
        if mapped:
            return normalize_kind(mapped)

    return normalize_kind(default_kind)


def identity_kind_for_record(
    record: ArchitectureRecord,
    config: ProjectConfig,
) -> str:
    return identity_kind_for_metadata(
        record.metadata,
        default_kind=config.id_default_kind,
        kind_map=config.id_kind_map,
    )


def identity_kind_for_new_record(kind: str, config: ProjectConfig) -> str:
    return normalize_kind(config.id_kind_map.get(kind, config.id_default_kind))


def id_segment_for_metadata(
    metadata: Mapping[str, object],
    *,
    default_segment: str,
    segment_map: Mapping[str, str],
) -> str:
    return identity_kind_for_metadata(
        metadata,
        default_kind=default_segment,
        kind_map=segment_map,
    )


def id_segment_for_record(record: ArchitectureRecord, config: ProjectConfig) -> str:
    return identity_kind_for_record(record, config)


def id_segment_for_new_record(kind: str, config: ProjectConfig) -> str:
    return identity_kind_for_new_record(kind, config)
