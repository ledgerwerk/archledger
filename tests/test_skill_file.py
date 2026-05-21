from __future__ import annotations

from pathlib import Path


def test_archledger_skill_exists() -> None:
    skill = Path("skills/archledger/SKILL.md")
    assert skill.is_file()
    text = skill.read_text(encoding="utf-8")
    assert "archledger --json paths" in text
    assert "archledger --json check" in text
    assert "archledger --json read --body" in text
    assert "archledger seed arc42-minimal" in text
    assert "generated build output" in text.lower()


def test_skill_file_mentions_markdown_and_asciidoc() -> None:
    text = Path("skills/archledger/SKILL.md").read_text(encoding="utf-8").lower()
    assert "markdown" in text
    assert "asciidoc" in text


def test_skill_file_instructs_read_without_export() -> None:
    text = Path("skills/archledger/SKILL.md").read_text(encoding="utf-8").lower()
    assert "archledger --json read --body" in text
    assert "configured build output directory" in text
    assert "source of truth" in text


def test_skill_file_does_not_call_markdown_legacy() -> None:
    text = Path("skills/archledger/SKILL.md").read_text(encoding="utf-8").lower()
    assert "markdown as legacy" not in text
    assert "treat markdown projects as legacy" not in text
