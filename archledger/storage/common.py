from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ledgercore.atomic import atomic_write_text
from ledgercore.io import normalize_newlines


def read_text(path: Path) -> str:
    """Read a text file and return its content with normalized newlines."""
    return normalize_newlines(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    """Write text to a file with normalized newlines, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalize_newlines(text), encoding="utf-8")


def ensure_dir(path: Path) -> None:
    """Create directory and parents if they do not exist."""
    path.mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def write_text_atomic(path: Path, text: str) -> None:
    atomic_write_text(path, text, normalize=True)
