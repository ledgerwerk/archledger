"""Ensure the checked-in CLI reference follows the shared inventory."""

from pathlib import Path

from archledger.cli_inventory import COMMAND_INVENTORY


def test_generated_cli_docs_match_inventory() -> None:
    document = (Path(__file__).parents[1] / "docs" / "cli-reference.md").read_text(
        encoding="utf-8"
    )
    missing = [
        entry.path
        for entry in COMMAND_INVENTORY.entries
        if f"`{entry.path}`" not in document
    ]
    assert not missing, f"CLI reference is missing inventory entries: {missing}"
