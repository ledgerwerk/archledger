from __future__ import annotations

from pathlib import Path

from archledger.storage.common import read_text, write_text_atomic


def test_write_text_atomic_replaces_contents_without_leaving_temp_files(
    tmp_path: Path,
) -> None:
    path = tmp_path / "demo.txt"

    write_text_atomic(path, "first\r\nline\r\n")
    write_text_atomic(path, "second\nline\n")

    assert read_text(path) == "second\nline\n"
    assert list(tmp_path.glob(".demo.txt.*.tmp")) == []
