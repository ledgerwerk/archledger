from __future__ import annotations

import pytest

from archledger.metadata_version import (
    MetadataVersionError,
    bump_metadata_version,
    metadata_version,
    require_version,
)


@pytest.mark.parametrize("value", [None, True, False, 0, -1, 1.0, "1"])
def test_require_version_rejects_non_positive_integers(value: object) -> None:
    with pytest.raises(MetadataVersionError, match="must be a positive integer"):
        require_version(value)


def test_metadata_version_uses_default_when_missing() -> None:
    assert metadata_version({}, default=3) == 3


def test_bump_metadata_version_preserves_metadata() -> None:
    assert bump_metadata_version({"id": "adr-0001", "version": 3}) == {
        "id": "adr-0001",
        "version": 4,
    }


def test_bump_metadata_version_treats_missing_legacy_version_as_one() -> None:
    assert bump_metadata_version({"id": "adr-0001"})["version"] == 2
