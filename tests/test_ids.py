from __future__ import annotations

from pathlib import Path

import pytest

from archledger.ids import (
    filename_for_ledger_id,
    format_ledger_id,
    is_ledger_id,
    ledger_id_from_filename,
    parse_ledger_id,
)


def test_format_ledger_id_zero_pads_numbers() -> None:
    assert format_ledger_id(1) == "al_0001"
    assert format_ledger_id(42) == "al_0042"


def test_format_ledger_id_rejects_invalid_numbers() -> None:
    for value in (0, -1, True):
        with pytest.raises(ValueError, match="positive integer"):
            format_ledger_id(value)  # type: ignore[arg-type]


def test_parse_ledger_id_roundtrip() -> None:
    record_id = format_ledger_id(123)
    assert parse_ledger_id(record_id) == 123


def test_parse_ledger_id_rejects_invalid_formats() -> None:
    for value in ("al_0000", "al_1", "AL_0001", "adr0001", "al-0001"):
        with pytest.raises(ValueError, match="Invalid ledger ID"):
            parse_ledger_id(value)


def test_is_ledger_id() -> None:
    assert is_ledger_id("al_0001")
    assert not is_ledger_id("requirement_0001")
    assert not is_ledger_id(1)


def test_filename_for_ledger_id() -> None:
    assert filename_for_ledger_id("al_0001", ".adoc") == "al_0001.adoc"

    with pytest.raises(ValueError, match="Invalid ledger ID"):
        filename_for_ledger_id("adr0001")


def test_ledger_id_from_filename() -> None:
    assert ledger_id_from_filename(Path("al_0007.adoc")) == "al_0007"

    with pytest.raises(ValueError, match="Invalid ledger ID"):
        ledger_id_from_filename(Path("requirement_0001.adoc"))
