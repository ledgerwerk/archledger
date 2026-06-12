from __future__ import annotations

from pathlib import Path

from ledgercore.atomic import atomic_write_text
from ledgercore.io import ensure_dir, read_text, write_text
from ledgercore.time import utc_now_iso


def write_text_atomic(path: Path, text: str) -> None:
    atomic_write_text(path, text, normalize=True)
