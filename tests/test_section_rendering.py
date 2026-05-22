from __future__ import annotations

from pathlib import Path

from archledger.dialects import get_dialect
from archledger.model import ArchitectureRecord
from archledger.section_rendering import building_block_hierarchy, section_diagrams


def test_building_block_hierarchy_omits_empty_fulfilled_requirements_and_risks() -> (
    None
):
    record = _black_box_record(fulfilled_requirements=[], risks=[])

    rendered = building_block_hierarchy([record], get_dialect("markdown"))

    assert "**Fulfilled requirements:**" not in rendered
    assert "**Risks:**" not in rendered


def test_building_block_hierarchy_renders_fulfilled_reqs_and_risks_when_present() -> (
    None
):
    record = _black_box_record(
        fulfilled_requirements=["al_0101"],
        risks=["al_0102"],
    )

    rendered = building_block_hierarchy([record], get_dialect("markdown"))

    assert "**Fulfilled requirements:** al_0101" in rendered
    assert "**Risks:** al_0102" in rendered


def _black_box_record(
    *,
    fulfilled_requirements: list[str],
    risks: list[str],
) -> ArchitectureRecord:
    return ArchitectureRecord(
        id="al_9999",
        type="black_box",
        title="Source Tracking Layer",
        status="accepted",
        section="building_block_view",
        order=9999,
        path=Path(".archledger/records/building_blocks/al_9999.md"),
        metadata={
            "level": 1,
            "parent": "al_0001",
            "interfaces": ["scan_workspace()"],
            "location": ["archledger/source_tracking.py"],
            "fulfilled_requirements": fulfilled_requirements,
            "risks": risks,
        },
        body="Source tracking details.",
    )


def test_section_diagrams_renders_diagram_body_and_caption() -> None:
    record = ArchitectureRecord(
        id="al_0201",
        type="diagram",
        title="Runtime login flow",
        status="accepted",
        section="runtime_view",
        order=10,
        path=Path(".archledger/records/diagrams/al_0201.md"),
        metadata={"caption": "Runtime login flow"},
        body="```mermaid\nflowchart LR\n  A --> B\n```",
    )

    rendered = section_diagrams([record], "runtime_view", get_dialect("markdown"))

    assert "## Runtime login flow" in rendered
    assert "```mermaid" in rendered
    assert "**Caption:** Runtime login flow" in rendered
