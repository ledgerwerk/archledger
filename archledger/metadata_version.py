from __future__ import annotations

from collections.abc import Mapping


class MetadataVersionError(ValueError):
    pass


def require_version(value: object, *, field_name: str = "version") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MetadataVersionError(f"{field_name} must be a positive integer.")
    return value


def metadata_version(metadata: Mapping[str, object], *, default: int = 1) -> int:
    value = metadata.get("version")
    if value is None:
        return default
    return require_version(value)


def bump_metadata_version(
    metadata: Mapping[str, object],
    *,
    default: int = 1,
) -> dict[str, object]:
    return {**metadata, "version": metadata_version(metadata, default=default) + 1}
