from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledgercore.refs import (
    LedgerResourceRef,
    parse_local_ref,
    parse_resource_ref,
)
from ledgercore.refs import (
    normalize_kind as normalize_resource_kind,
)

DEFAULT_ID_PREFIX = "al"
DEFAULT_LEDGER_CODE = DEFAULT_ID_PREFIX
DEFAULT_ID_WIDTH = 4
DEFAULT_ID_SEGMENT_MODE = "none"
VALID_ID_SEGMENT_MODES: frozenset[str] = frozenset({"none", "type"})
ID_PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9]{1,15}$")
ID_SEGMENT_PATTERN = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
_WORD_CHAR_CLASS = "A-Za-z0-9"


@dataclass(frozen=True, slots=True)
class ParsedLedgerId:
    number: int
    segment: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedRecordId:
    kind: str
    number: int
    ledger: str | None = None


@dataclass(frozen=True, slots=True)
class LedgerIdFormat:
    prefix: str = DEFAULT_ID_PREFIX
    width: int = DEFAULT_ID_WIDTH
    segment_mode: str = DEFAULT_ID_SEGMENT_MODE

    def __post_init__(self) -> None:
        validate_id_prefix(self.prefix)
        validate_id_width(self.width)
        validate_id_segment_mode(self.segment_mode)

    @property
    def pattern_text(self) -> str:
        escaped = re.escape(self.prefix)
        if self.segment_mode == "none":
            return rf"^{escaped}_(?P<number>\d{{{self.width},}})$"
        return (
            rf"^{escaped}_"
            rf"(?P<segment>[a-z][a-z0-9-]{{1,31}})_"
            rf"(?P<number>\d{{{self.width},}})$"
        )

    @property
    def reference_pattern_text(self) -> str:
        escaped = re.escape(self.prefix)
        if self.segment_mode == "none":
            return (
                rf"(?<![{_WORD_CHAR_CLASS}])"
                rf"{escaped}_(?P<number>\d{{{self.width},}})"
                rf"(?![{_WORD_CHAR_CLASS}])"
            )
        return (
            rf"(?<![{_WORD_CHAR_CLASS}])"
            rf"{escaped}_"
            rf"(?P<segment>[a-z][a-z0-9-]{{1,31}})_"
            rf"(?P<number>\d{{{self.width},}})"
            rf"(?![{_WORD_CHAR_CLASS}])"
        )

    def pattern(self) -> re.Pattern[str]:
        return re.compile(self.pattern_text)

    def reference_pattern(self) -> re.Pattern[str]:
        return re.compile(self.reference_pattern_text)

    def format(self, number: int, *, segment: str | None = None) -> str:
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            raise ValueError("Ledger ID number must be a positive integer.")
        if self.segment_mode == "none":
            return f"{self.prefix}_{number:0{self.width}d}"
        if segment is None:
            raise ValueError("Segmented ledger IDs require a segment.")
        validated_segment = validate_id_segment(segment)
        return f"{self.prefix}_{validated_segment}_{number:0{self.width}d}"

    def parse_parts(self, record_id: str) -> ParsedLedgerId:
        match = self.pattern().fullmatch(record_id)
        if match is None:
            raise ValueError(f"Invalid ledger ID: {record_id!r}")
        number = int(match.group("number"))
        if number < 1:
            raise ValueError(f"Invalid ledger ID: {record_id!r}")
        segment = match.groupdict().get("segment")
        return ParsedLedgerId(
            number=number,
            segment=None if segment is None else validate_id_segment(segment),
        )

    def parse(self, record_id: str) -> int:
        return self.parse_parts(record_id).number

    def is_id(self, value: object) -> bool:
        return is_ledger_id(
            value,
            prefix=self.prefix,
            width=self.width,
            segment_mode=self.segment_mode,
        )


def validate_id_prefix(prefix: str) -> str:
    normalized = prefix.strip()
    if not ID_PREFIX_PATTERN.fullmatch(normalized):
        raise ValueError("Ledger ID prefix must match ^[a-z][a-z0-9]{1,15}$.")
    return normalized


def validate_id_width(width: int) -> int:
    if isinstance(width, bool) or not isinstance(width, int) or not 2 <= width <= 12:
        raise ValueError("Ledger ID width must be an integer from 2 to 12.")
    return width


def validate_id_segment_mode(segment_mode: str) -> str:
    normalized = segment_mode.strip().lower()
    if normalized not in VALID_ID_SEGMENT_MODES:
        raise ValueError("Ledger ID segment mode must be one of: none, type.")
    return normalized


def validate_id_segment(segment: str) -> str:
    normalized = segment.strip().lower()
    if not ID_SEGMENT_PATTERN.fullmatch(normalized):
        raise ValueError("Ledger ID segment must match ^[a-z][a-z0-9-]{1,31}$.")
    return normalized


def format_ledger_id(
    number: int,
    *,
    prefix: str = DEFAULT_ID_PREFIX,
    width: int = DEFAULT_ID_WIDTH,
    segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
    segment: str | None = None,
) -> str:
    return LedgerIdFormat(
        prefix=prefix,
        width=width,
        segment_mode=segment_mode,
    ).format(number, segment=segment)


def parse_ledger_id_parts(
    record_id: str,
    *,
    prefix: str = DEFAULT_ID_PREFIX,
    width: int = DEFAULT_ID_WIDTH,
    segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
) -> ParsedLedgerId:
    return LedgerIdFormat(
        prefix=prefix,
        width=width,
        segment_mode=segment_mode,
    ).parse_parts(record_id)


def parse_ledger_id(
    record_id: str,
    *,
    prefix: str = DEFAULT_ID_PREFIX,
    width: int = DEFAULT_ID_WIDTH,
    segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
) -> int:
    return parse_ledger_id_parts(
        record_id,
        prefix=prefix,
        width=width,
        segment_mode=segment_mode,
    ).number


def is_ledger_id(
    value: object,
    *,
    prefix: str = DEFAULT_ID_PREFIX,
    width: int = DEFAULT_ID_WIDTH,
    segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parse_ledger_id(
            value,
            prefix=prefix,
            width=width,
            segment_mode=segment_mode,
        )
    except ValueError:
        return False
    return True


def filename_for_ledger_id(
    record_id: str,
    extension: str = ".md",
    *,
    prefix: str = DEFAULT_ID_PREFIX,
    width: int = DEFAULT_ID_WIDTH,
    segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
) -> str:
    parse_ledger_id(
        record_id,
        prefix=prefix,
        width=width,
        segment_mode=segment_mode,
    )
    return f"{record_id}{extension}"


def ledger_id_from_filename(
    path: Path,
    *,
    prefix: str = DEFAULT_ID_PREFIX,
    width: int = DEFAULT_ID_WIDTH,
    segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
) -> str:
    record_id = path.stem
    parse_ledger_id(
        record_id,
        prefix=prefix,
        width=width,
        segment_mode=segment_mode,
    )
    return record_id


def format_local_id(kind: str, number: int, *, width: int = DEFAULT_ID_WIDTH) -> str:
    normalized_kind = normalize_resource_kind(kind)
    return f"{normalized_kind}-{number:0{validate_id_width(width)}d}"


def parse_record_id(value: str, *, width: int = DEFAULT_ID_WIDTH) -> ParsedRecordId:
    ref = parse_local_ref(value, width=width)
    return ParsedRecordId(kind=ref.kind, number=ref.number, ledger=ref.ledger)


def parse_record_ref(
    value: str,
    *,
    default_ledger: str | None = None,
    width: int = DEFAULT_ID_WIDTH,
) -> LedgerResourceRef:
    return parse_resource_ref(
        value,
        default_ledger=default_ledger,
        width=width,
        allow_legacy_alias=True,
    )


def parse_legacy_archledger_id(
    value: str,
    *,
    ledger_code: str = DEFAULT_LEDGER_CODE,
    width: int = DEFAULT_ID_WIDTH,
) -> LedgerResourceRef:
    return parse_resource_ref(
        value,
        default_ledger=ledger_code,
        width=width,
        allow_legacy_alias=True,
    )


def global_ref_for(
    record_id: str,
    ledger_code: str,
    *,
    width: int = DEFAULT_ID_WIDTH,
) -> str:
    ref = parse_local_ref(record_id, width=width).with_ledger(ledger_code)
    return ref.global_ref


def file_ref_for(
    record_id: str,
    ledger_code: str,
    *,
    width: int = DEFAULT_ID_WIDTH,
) -> str:
    ref = parse_local_ref(record_id, width=width).with_ledger(ledger_code)
    return ref.file_ref
