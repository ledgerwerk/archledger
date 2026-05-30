from __future__ import annotations

from pathlib import Path

import pytest

from archledger.ids import (
    LedgerIdFormat,
    filename_for_ledger_id,
    format_ledger_id,
    is_ledger_id,
    ledger_id_from_filename,
    parse_ledger_id,
    parse_ledger_id_parts,
    validate_id_prefix,
    validate_id_segment,
    validate_id_segment_mode,
    validate_id_width,
)


def test_format_ledger_id_zero_pads_numbers() -> None:
    assert format_ledger_id(1) == "al_0001"
    assert format_ledger_id(42) == "al_0042"


def test_format_ledger_id_uses_configurable_prefix_and_width() -> None:
    assert format_ledger_id(1, prefix="ta", width=3) == "ta_001"
    assert format_ledger_id(112, prefix="ta", width=3) == "ta_112"
    assert format_ledger_id(1000, prefix="ta", width=3) == "ta_1000"


def test_format_ledger_id_rejects_invalid_numbers() -> None:
    for value in (0, -1):
        with pytest.raises(ValueError, match="positive integer"):
            format_ledger_id(value)
    with pytest.raises(ValueError, match="positive integer"):
        format_ledger_id(True)


def test_parse_ledger_id_roundtrip() -> None:
    record_id = format_ledger_id(123)
    assert parse_ledger_id(record_id) == 123


def test_parse_ledger_id_uses_configurable_prefix_and_width() -> None:
    assert parse_ledger_id("ta_001", prefix="ta", width=3) == 1
    assert parse_ledger_id("ta_1000", prefix="ta", width=3) == 1000


def test_parse_ledger_id_rejects_wrong_configured_format() -> None:
    with pytest.raises(ValueError):
        parse_ledger_id("al_0001", prefix="ta", width=3)
    with pytest.raises(ValueError):
        parse_ledger_id("ta_01", prefix="ta", width=3)


def test_parse_ledger_id_rejects_invalid_formats() -> None:
    for value in ("al_0000", "al_1", "AL_0001", "adr0001", "al-0001"):
        with pytest.raises(ValueError, match="Invalid ledger ID"):
            parse_ledger_id(value)


def test_is_ledger_id() -> None:
    assert is_ledger_id("al_0001")
    assert is_ledger_id("ta_001", prefix="ta", width=3)
    assert not is_ledger_id("requirement_0001")
    assert not is_ledger_id(1)


def test_filename_for_ledger_id() -> None:
    assert filename_for_ledger_id("al_0001", ".adoc") == "al_0001.adoc"

    with pytest.raises(ValueError, match="Invalid ledger ID"):
        filename_for_ledger_id("adr0001")


def test_ledger_id_from_filename() -> None:
    assert ledger_id_from_filename(Path("al_0007.adoc")) == "al_0007"
    assert (
        ledger_id_from_filename(Path("ta_007.adoc"), prefix="ta", width=3) == "ta_007"
    )

    with pytest.raises(ValueError, match="Invalid ledger ID"):
        ledger_id_from_filename(Path("requirement_0001.adoc"))


def test_validate_prefix_and_width() -> None:
    assert validate_id_prefix("ta") == "ta"
    assert validate_id_prefix(" t17 ") == "t17"
    assert validate_id_width(3) == 3
    assert validate_id_segment_mode("none") == "none"
    assert validate_id_segment_mode(" type ") == "type"
    assert validate_id_segment(" quality-risk ") == "quality-risk"

    with pytest.raises(ValueError, match="prefix"):
        validate_id_prefix("TA")
    with pytest.raises(ValueError, match="width"):
        validate_id_width(1)
    with pytest.raises(ValueError, match="segment mode"):
        validate_id_segment_mode("prefix")
    with pytest.raises(ValueError, match="segment must match"):
        validate_id_segment("risk_critical")


def test_ledger_id_format_helpers() -> None:
    fmt = LedgerIdFormat(prefix="ta", width=3)
    assert fmt.pattern_text == r"^ta_(?P<number>\d{3,})$"
    assert fmt.format(12) == "ta_012"
    assert fmt.parse("ta_999") == 999
    assert fmt.is_id("ta_111")


def test_format_ledger_id_with_segment() -> None:
    fmt = LedgerIdFormat(prefix="al", width=4, segment_mode="type")
    assert fmt.format(4, segment="content") == "al_content_0004"
    assert fmt.format(5, segment="risk") == "al_risk_0005"


def test_parse_segmented_ledger_id_returns_number_and_segment() -> None:
    fmt = LedgerIdFormat(prefix="al", width=4, segment_mode="type")
    parsed = fmt.parse_parts("al_risk_0005")
    assert parsed.number == 5
    assert parsed.segment == "risk"
    assert fmt.parse("al_risk_0005") == 5
    parsed_wrapper = parse_ledger_id_parts(
        "al_risk_0005",
        segment_mode="type",
    )
    assert parsed_wrapper.number == 5
    assert parsed_wrapper.segment == "risk"


def test_segment_mode_none_rejects_segmented_id() -> None:
    fmt = LedgerIdFormat(prefix="al", width=4, segment_mode="none")
    assert not fmt.is_id("al_content_0004")
    with pytest.raises(ValueError, match="Invalid ledger ID"):
        parse_ledger_id("al_content_0004", segment_mode="none")


def test_segment_mode_type_rejects_unsegmented_id() -> None:
    fmt = LedgerIdFormat(prefix="al", width=4, segment_mode="type")
    assert not fmt.is_id("al_0004")
    with pytest.raises(ValueError, match="Invalid ledger ID"):
        parse_ledger_id("al_0004", segment_mode="type")


def test_segment_mode_type_requires_segment_for_format() -> None:
    fmt = LedgerIdFormat(prefix="al", width=4, segment_mode="type")
    with pytest.raises(ValueError, match="require a segment|require.*segment"):
        fmt.format(4)


def test_format_ledger_id_ignores_segment_when_mode_none() -> None:
    assert format_ledger_id(42, segment_mode="none", segment="risk") == "al_0042"
