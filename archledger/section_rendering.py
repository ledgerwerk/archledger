from __future__ import annotations

from archledger.dialects import Dialect
from archledger.model import ArchitectureRecord, record_sort_key


def section_body(
    sections: dict[str, ArchitectureRecord],
    section_key: str,
    dialect: Dialect,
) -> str:
    record = sections.get(section_key)
    if record is None:
        return dialect.placeholder()
    body = record.body.strip()
    if not body or body == dialect.section_placeholder:
        return dialect.placeholder()
    return body


def requirements_overview(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    requirements = _records_of_type(records, "requirement")
    rows = [
        [
            record.title,
            str(record.metadata.get("priority", "")),
            str(record.metadata.get("source", "")),
            ", ".join(_string_list(record.metadata.get("stakeholders"))),
            ", ".join(_string_list(record.metadata.get("quality_goals"))),
        ]
        for record in requirements
    ]
    return dialect.table(
        ["Title", "Priority", "Source", "Stakeholders", "Quality goals"],
        rows,
    )


def quality_goals_table(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    quality_goals = _records_of_type(records, "quality_goal")
    rows = [
        [
            record.title,
            str(record.metadata.get("priority", "")),
            _compact_text(record.metadata.get("scenario")),
        ]
        for record in quality_goals
    ]
    return dialect.table(["Title", "Priority", "Scenario"], rows)


def stakeholders_table(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    stakeholders = _records_of_type(records, "stakeholder")
    rows = [
        [
            record.title,
            str(record.metadata.get("contact", "")),
            ", ".join(_string_list(record.metadata.get("expectations"))),
        ]
        for record in stakeholders
    ]
    return dialect.table(["Title", "Contact", "Expectations"], rows)


def constraints_list(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    constraints = _records_of_type(records, "constraint")
    if not constraints:
        return dialect.placeholder()
    lines: list[str] = []
    for record in constraints:
        lines.extend(
            [
                dialect.bullet(dialect.strong(record.title)),
                dialect.bullet(f"Impact: {record.metadata.get('impact', '')}", depth=1),
            ]
        )
        body = record.body.strip()
        if body:
            lines.append(dialect.bullet(f"Notes: {body}", depth=1))
    return "\n".join(lines)


def context_interfaces(
    records: list[ArchitectureRecord],
    context_kind: str,
    dialect: Dialect,
) -> str:
    interfaces = [
        record
        for record in _records_of_type(records, "context_interface")
        if record.metadata.get("context_kind") == context_kind
    ]
    if not interfaces:
        return dialect.placeholder()
    lines: list[str] = []
    for record in interfaces:
        lines.append(
            dialect.bullet(
                f"{dialect.strong(record.title)} -> "
                f"{record.metadata.get('partner', '')}"
            )
        )
        body = record.body.strip()
        if body:
            lines.append(dialect.bullet(body, depth=1))
    return "\n".join(lines)


def solution_strategy_items(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    items = _records_of_type(records, "strategy_item")
    if not items:
        return dialect.placeholder()
    lines: list[str] = []
    for record in items:
        drivers = ", ".join(_string_list(record.metadata.get("drivers")))
        constraints = ", ".join(_string_list(record.metadata.get("constraints")))
        related_adrs = ", ".join(_string_list(record.metadata.get("related_adrs")))
        lines.extend(
            [
                dialect.heading(dialect.record_heading_level, record.title),
                "",
                f"{dialect.strong('Drivers:')} {drivers}",
                f"{dialect.strong('Constraints:')} {constraints}",
                f"{dialect.strong('Related ADRs:')} {related_adrs}",
                "",
                record.body.strip() or dialect.placeholder(),
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def section_diagrams(
    records: list[ArchitectureRecord],
    section_key: str,
    dialect: Dialect,
) -> str:
    diagrams = [
        record
        for record in _records_of_type(records, "diagram")
        if record.section == section_key
    ]
    if not diagrams:
        return ""
    lines: list[str] = []
    for record in diagrams:
        caption = (
            str(record.metadata.get("caption", record.title)).strip() or record.title
        )
        lines.extend(
            [
                dialect.heading(dialect.record_heading_level, record.title),
                "",
                record.body.strip() or dialect.placeholder(),
                "",
                f"{dialect.strong('Caption:')} {caption}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def building_block_hierarchy(
    records: list[ArchitectureRecord], dialect: Dialect
) -> str:
    white_boxes = _records_of_type(records, "white_box")
    black_boxes = _records_of_type(records, "black_box")
    interfaces = _records_of_type(records, "interface")
    if not white_boxes and not black_boxes and not interfaces:
        return dialect.placeholder()

    lines: list[str] = []
    for record in white_boxes:
        lines.extend(
            [
                dialect.heading(
                    dialect.record_heading_level,
                    f"Whitebox {record.title}",
                ),
                "",
                record.body.strip() or dialect.placeholder(),
                "",
            ]
        )
    black_box_levels = sorted(
        {
            level
            for level in (record.metadata.get("level") for record in black_boxes)
            if isinstance(level, int) and not isinstance(level, bool)
        }
    )
    for level in black_box_levels:
        lines.extend(
            [dialect.heading(dialect.record_heading_level + 1, f"Level {level}"), ""]
        )
        for record in black_boxes:
            if record.metadata.get("level") != level:
                continue
            interfaces_value = ", ".join(
                _string_list(record.metadata.get("interfaces"))
            )
            locations = ", ".join(_string_list(record.metadata.get("location")))
            fulfilled_requirements = ", ".join(
                _string_list(record.metadata.get("fulfilled_requirements"))
            )
            risks = ", ".join(_string_list(record.metadata.get("risks")))
            metadata_lines = [
                f"{dialect.strong('Parent:')} {record.metadata.get('parent', '')}",
                f"{dialect.strong('Interfaces:')} {interfaces_value}",
                f"{dialect.strong('Location:')} {locations}",
            ]
            if fulfilled_requirements:
                metadata_lines.append(
                    f"{dialect.strong('Fulfilled requirements:')} "
                    f"{fulfilled_requirements}"
                )
            if risks:
                metadata_lines.append(f"{dialect.strong('Risks:')} {risks}")
            lines.extend(
                [
                    dialect.heading(dialect.record_heading_level + 2, record.title),
                    "",
                    *metadata_lines,
                    "",
                    record.body.strip() or dialect.placeholder(),
                    "",
                ]
            )
    if interfaces:
        lines.extend([dialect.heading(dialect.record_heading_level, "Interfaces"), ""])
        for record in interfaces:
            providers = ", ".join(_string_list(record.metadata.get("providers")))
            consumers = ", ".join(_string_list(record.metadata.get("consumers")))
            lines.extend(
                [
                    dialect.heading(dialect.record_heading_level + 1, record.title),
                    "",
                    f"{dialect.strong('Providers:')} {providers}",
                    f"{dialect.strong('Consumers:')} {consumers}",
                    f"{dialect.strong('Protocol:')} "
                    f"{record.metadata.get('protocol', '')}"
                    "",
                    record.body.strip() or dialect.placeholder(),
                    "",
                ]
            )
    return "\n".join(lines).rstrip()


def adr_sections(
    records: list[ArchitectureRecord],
    dialect: Dialect,
    *,
    document_version: int,
) -> str:
    adrs = _records_of_type(records, "adr")
    if not adrs:
        return dialect.placeholder()
    lines: list[str] = []
    for record in adrs:
        lines.append("")
        lines.extend(
            [
                dialect.heading(dialect.record_heading_level, record.title),
                "",
                f"{dialect.strong('Document version:')} {document_version}",
                "",
                record.body.strip() or dialect.placeholder(),
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def render_named_records(
    records: list[ArchitectureRecord],
    record_type: str,
    dialect: Dialect,
) -> str:
    matching = _records_of_type(records, record_type)
    if not matching:
        return dialect.placeholder()
    lines: list[str] = []
    for record in matching:
        lines.extend(
            [
                dialect.heading(dialect.record_heading_level, record.title),
                "",
                record.body.strip() or dialect.placeholder(),
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def runtime_scenarios(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    return render_named_records(records, "runtime_scenario", dialect)


def deployment_view(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    return render_named_records(records, "infrastructure", dialect)


def concepts(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    return render_named_records(records, "concept", dialect)


def quality_scenarios(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    scenarios = _records_of_type(records, "quality_scenario")
    rows = [
        [
            record.title,
            str(record.metadata.get("quality", "")),
            str(record.metadata.get("stimulus", "")),
            str(record.metadata.get("response_measure", "")),
        ]
        for record in scenarios
    ]
    return dialect.table(["Title", "Quality", "Stimulus", "Response measure"], rows)


def quality_requirements_overview(
    records: list[ArchitectureRecord],
    dialect: Dialect,
) -> str:
    requirements = _records_of_type(records, "quality_requirement")
    rows = [
        [
            record.title,
            str(record.metadata.get("category", "")),
            str(record.metadata.get("measure", "")),
            ", ".join(_string_list(record.metadata.get("scenarios"))),
        ]
        for record in requirements
    ]
    return dialect.table(["Title", "Category", "Measure", "Scenarios"], rows)


def risk_table(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    risks = _records_of_type(records, "risk")
    rows = [
        [
            record.title,
            str(record.metadata.get("severity", "")),
            str(record.metadata.get("probability", "")),
            str(record.metadata.get("mitigation", "")),
            _compact_text(record.body),
        ]
        for record in risks
    ]
    return dialect.table(
        ["Title", "Severity", "Probability", "Mitigation", "Notes"], rows
    )


def glossary_table(records: list[ArchitectureRecord], dialect: Dialect) -> str:
    terms = _records_of_type(records, "glossary_term")
    rows = [
        [
            str(record.metadata.get("term", record.title)),
            str(record.metadata.get("definition", "")),
        ]
        for record in terms
    ]
    return dialect.table(["Term", "Definition"], rows)


def _records_of_type(
    records: list[ArchitectureRecord],
    record_type: str,
) -> list[ArchitectureRecord]:
    return sorted(
        [record for record in records if record.type == record_type],
        key=record_sort_key,
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _compact_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())
