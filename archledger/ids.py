from __future__ import annotations

import re
from pathlib import Path

LEDGER_ID_PREFIX = "al"
LEDGER_ID_PATTERN = re.compile(r"^al_(?P<number>\d{4})$")


def format_ledger_id(number: int) -> str:
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise ValueError("Ledger ID number must be a positive integer.")
    return f"{LEDGER_ID_PREFIX}_{number:04d}"


def parse_ledger_id(record_id: str) -> int:
    match = LEDGER_ID_PATTERN.fullmatch(record_id)
    if match is None:
        raise ValueError(f"Invalid ledger ID: {record_id!r}")
    number = int(match.group("number"))
    if number < 1:
        raise ValueError(f"Invalid ledger ID: {record_id!r}")
    return number


def is_ledger_id(value: object) -> bool:
    return isinstance(value, str) and LEDGER_ID_PATTERN.fullmatch(value) is not None


def filename_for_ledger_id(record_id: str, extension: str = ".md") -> str:
    parse_ledger_id(record_id)
    return f"{record_id}{extension}"


def ledger_id_from_filename(path: Path) -> str:
    record_id = path.stem
    parse_ledger_id(record_id)
    return record_id
