from __future__ import annotations

from pathlib import Path

from ledgercore.atomic import atomic_write_text


def write_text_atomic(path: Path, text: str) -> None:
    atomic_write_text(path, text, normalize=True)
