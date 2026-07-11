from __future__ import annotations

from pathlib import Path


def test_archledger_skill_exists() -> None:
    skill = Path("skills/archledger/SKILL.md")
    assert skill.is_file()
    text = skill.read_text(encoding="utf-8")
    assert "archledger --json context" in text
    assert "archledger --json trace" in text
    assert "archledger --json read" in text
    assert "archledger --json check" in text
    assert "archledger --json source changed" in text
    assert "archledger --json migrate ids --to ledgercore" in text
    assert "archledger --json migrate metadata --to versioned" in text
    assert "--json-value" in text
    assert "archledger --json check --strict" in text
    assert "archledger --json source changed --fail-on-unlinked" in text
    assert "archledger --json source snapshot" in text
    assert "capture" in text.lower() and "result.id" in text
    assert "isolated architecture ledger" in text.lower()
    assert "never predict record ids" in text.lower()


def test_skill_file_removes_sdd_bdd_command_guidance() -> None:
    text = Path("skills/archledger/SKILL.md").read_text(encoding="utf-8").lower()
    assert "archledger sdd" not in text
    assert "archledger bdd" not in text
    assert "gherkin" not in text
    assert "specweave" not in text
