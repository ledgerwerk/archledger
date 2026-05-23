from __future__ import annotations

from collections.abc import Mapping

from archledger.ids import validate_id_segment
from archledger.model import ArchitectureRecord
from archledger.storage.project_config import ProjectConfig


def id_segment_for_metadata(
    metadata: Mapping[str, object],
    *,
    default_segment: str,
    segment_map: Mapping[str, str],
) -> str:
    explicit = metadata.get("id_segment")
    if isinstance(explicit, str) and explicit.strip():
        return validate_id_segment(explicit)

    record_type = metadata.get("type")
    if isinstance(record_type, str):
        mapped = segment_map.get(record_type)
        if mapped:
            return validate_id_segment(mapped)

    return validate_id_segment(default_segment)


def id_segment_for_record(
    record: ArchitectureRecord,
    config: ProjectConfig,
) -> str:
    return id_segment_for_metadata(
        record.metadata,
        default_segment=config.id_default_segment,
        segment_map=config.id_segment_map,
    )


def id_segment_for_new_record(kind: str, config: ProjectConfig) -> str:
    return validate_id_segment(
        config.id_segment_map.get(kind, config.id_default_segment)
    )
