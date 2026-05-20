from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from archledger import __version__
from archledger.errors import RenderError
from archledger.model import ArchitectureRecord, is_visible_status, record_sort_key
from archledger.repository import ArchitectureRepository
from archledger.storage.common import utc_now_iso, write_text

EMPTY_PLACEHOLDER = "<!-- archledger: no accepted records for this section yet -->"


@dataclass(frozen=True, slots=True)
class AssemblyResult:
    output_path: Path
    rendered_text: str
    source_format: str = "asciidoc"


def assemble_asciidoc_document(
    repo: ArchitectureRepository,
    *,
    output: Path | None = None,
    include_draft: bool = False,
    include_superseded: bool = False,
    strict: bool = False,
) -> AssemblyResult:
    check_result = repo.check(strict=strict, repair_counters=False)
    if check_result.has_failures(strict=strict):
        raise RenderError(
            f"Build blocked by {len(check_result.errors)} error(s) and "
            f"{len(check_result.warnings)} warning(s)."
        )

    all_records = repo.load_all_records(include_sections=True)
    sections = {
        record.section: record
        for record in all_records
        if record.type == "section"
    }
    records = [
        record
        for record in all_records
        if record.type != "section"
        and is_visible_status(
            record.status,
            include_draft=include_draft,
            include_superseded=include_superseded,
        )
    ]

    env = Environment(
        loader=PackageLoader("archledger", "templates"),
        autoescape=select_autoescape(
            enabled_extensions=(),
            default_for_string=False,
        ),
        keep_trailing_newline=True,
    )
    template = env.get_template("arc42_document.adoc.j2")
    rendered = template.render(
        title=repo.config.arc42_title,
        date=utc_now_iso()[:10],
        generator=f"archledger {__version__}",
        arc42_template_version=repo.config.arc42_template_version,
        section_body=lambda section_key: _section_body(sections, section_key),
        requirements_overview=lambda: _requirements_overview(records),
        quality_goals_table=lambda: _quality_goals_table(records),
        stakeholders_table=lambda: _stakeholders_table(records),
        constraints_list=lambda: _constraints_list(records),
        context_interfaces=lambda context_kind: _context_interfaces(
            records,
            context_kind,
        ),
        solution_strategy_items=lambda: _solution_strategy_items(records),
        building_block_hierarchy=lambda: _building_block_hierarchy(records),
        runtime_scenarios=lambda: _render_named_records(
            records,
            "runtime_scenario",
            "===",
        ),
        deployment_view=lambda: _render_named_records(
            records,
            "infrastructure",
            "===",
        ),
        concepts=lambda: _render_named_records(records, "concept", "==="),
        adr_sections=lambda: _adr_sections(records),
        quality_requirements_overview=lambda: _quality_requirements_overview(records),
        quality_scenarios=lambda: _quality_scenarios(records),
        risk_table=lambda: _risk_table(records),
        glossary_table=lambda: _glossary_table(records),
    )
    output_path = _resolve_output_path(repo, output)
    write_text(output_path, rendered)
    return AssemblyResult(output_path=output_path, rendered_text=rendered)


def _resolve_output_path(repo: ArchitectureRepository, output: Path | None) -> Path:
    if output is None:
        return repo.paths.build_dir / repo.config.build_default_output
    if output.is_absolute():
        return output
    return repo.paths.workspace_root / output


def _section_body(
    sections: dict[str, ArchitectureRecord],
    section_key: str,
) -> str:
    record = sections.get(section_key)
    if record is None:
        return EMPTY_PLACEHOLDER
    body = record.body.strip()
    if not body or body == "<!-- archledger: add section-level prose here -->":
        return EMPTY_PLACEHOLDER
    return body


def _requirements_overview(records: list[ArchitectureRecord]) -> str:
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
    return _asciidoc_table(
        ["Title", "Priority", "Source", "Stakeholders", "Quality goals"],
        rows,
    )


def _quality_goals_table(records: list[ArchitectureRecord]) -> str:
    quality_goals = _records_of_type(records, "quality_goal")
    rows = [
        [
            record.title,
            str(record.metadata.get("priority", "")),
            _compact_text(record.metadata.get("scenario")),
        ]
        for record in quality_goals
    ]
    return _asciidoc_table(["Title", "Priority", "Scenario"], rows)


def _stakeholders_table(records: list[ArchitectureRecord]) -> str:
    stakeholders = _records_of_type(records, "stakeholder")
    rows = [
        [
            record.title,
            str(record.metadata.get("contact", "")),
            ", ".join(_string_list(record.metadata.get("expectations"))),
        ]
        for record in stakeholders
    ]
    return _asciidoc_table(["Title", "Contact", "Expectations"], rows)


def _constraints_list(records: list[ArchitectureRecord]) -> str:
    constraints = _records_of_type(records, "constraint")
    if not constraints:
        return EMPTY_PLACEHOLDER
    chunks: list[str] = []
    for record in constraints:
        chunks.extend(
            [
                f"* *{record.title}*",
                f"** Impact: {record.metadata.get('impact', '')}",
            ]
        )
        body = record.body.strip()
        if body:
            chunks.append(f"** Notes: {body}")
    return "\n".join(chunks)


def _context_interfaces(records: list[ArchitectureRecord], context_kind: str) -> str:
    interfaces = [
        record
        for record in _records_of_type(records, "context_interface")
        if record.metadata.get("context_kind") == context_kind
    ]
    if not interfaces:
        return EMPTY_PLACEHOLDER
    lines: list[str] = []
    for record in interfaces:
        lines.append(f"* *{record.title}* -> {record.metadata.get('partner', '')}")
        body = record.body.strip()
        if body:
            lines.append(f"** {body}")
    return "\n".join(lines)


def _solution_strategy_items(records: list[ArchitectureRecord]) -> str:
    items = _records_of_type(records, "strategy_item")
    if not items:
        return EMPTY_PLACEHOLDER

    lines: list[str] = []
    for record in items:
        drivers = ", ".join(_string_list(record.metadata.get("drivers")))
        constraints = ", ".join(_string_list(record.metadata.get("constraints")))
        related_adrs = ", ".join(_string_list(record.metadata.get("related_adrs")))
        lines.extend(
            [
                f"==== {record.title}",
                "",
                f"*Drivers:* {drivers}",
                f"*Constraints:* {constraints}",
                f"*Related ADRs:* {related_adrs}",
                "",
                record.body.strip() or EMPTY_PLACEHOLDER,
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _building_block_hierarchy(records: list[ArchitectureRecord]) -> str:
    white_boxes = _records_of_type(records, "white_box")
    black_boxes = _records_of_type(records, "black_box")
    interfaces = _records_of_type(records, "interface")
    if not white_boxes and not black_boxes and not interfaces:
        return EMPTY_PLACEHOLDER

    lines: list[str] = []
    for record in white_boxes:
        lines.extend(
            [
                f"=== Whitebox {record.title}",
                "",
                record.body.strip() or EMPTY_PLACEHOLDER,
                "",
            ]
        )
    black_box_levels = sorted(
        {
            level
            for level in (
                record.metadata.get("level")
                for record in black_boxes
            )
            if isinstance(level, int) and not isinstance(level, bool)
        }
    )
    for level in black_box_levels:
        lines.extend([f"==== Level {level}", ""])
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
            lines.extend(
                [
                    f"===== {record.title}",
                    "",
                    f"*Parent:* {record.metadata.get('parent', '')}",
                    f"*Interfaces:* {interfaces_value}",
                    f"*Location:* {locations}",
                    f"*Fulfilled requirements:* {fulfilled_requirements}",
                    f"*Risks:* {risks}",
                    "",
                    record.body.strip() or EMPTY_PLACEHOLDER,
                    "",
                ]
            )
    if interfaces:
        lines.extend(["=== Interfaces", ""])
        for record in interfaces:
            providers = ", ".join(_string_list(record.metadata.get("providers")))
            consumers = ", ".join(_string_list(record.metadata.get("consumers")))
            lines.extend(
                [
                    f"==== {record.title}",
                    "",
                    f"*Providers:* {providers}",
                    f"*Consumers:* {consumers}",
                    f"*Protocol:* {record.metadata.get('protocol', '')}",
                    "",
                    record.body.strip() or EMPTY_PLACEHOLDER,
                    "",
                ]
            )
    return "\n".join(lines).rstrip()


def _adr_sections(records: list[ArchitectureRecord]) -> str:
    adrs = _records_of_type(records, "adr")
    if not adrs:
        return EMPTY_PLACEHOLDER
    lines: list[str] = []
    for record in adrs:
        deciders = ", ".join(_string_list(record.metadata.get("deciders")))
        supersedes = ", ".join(_string_list(record.metadata.get("supersedes")))
        related = ", ".join(_string_list(record.metadata.get("related")))
        lines.append("")
        lines.extend(
            [
                f"=== {record.title}",
                "",
                f"*Status:* {record.status}",
                f"*Date:* {record.metadata.get('date', '')}",
                f"*Deciders:* {deciders}",
                f"*Supersedes:* {supersedes}",
                f"*Related:* {related}",
                "",
                record.body.strip() or EMPTY_PLACEHOLDER,
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _render_named_records(
    records: list[ArchitectureRecord],
    record_type: str,
    heading_prefix: str,
) -> str:
    matching = _records_of_type(records, record_type)
    if not matching:
        return EMPTY_PLACEHOLDER
    lines: list[str] = []
    for record in matching:
        lines.extend(
            [
                f"{heading_prefix} {record.title}",
                "",
                record.body.strip() or EMPTY_PLACEHOLDER,
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _quality_scenarios(records: list[ArchitectureRecord]) -> str:
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
    return _asciidoc_table(
        ["Title", "Quality", "Stimulus", "Response measure"],
        rows,
    )


def _quality_requirements_overview(records: list[ArchitectureRecord]) -> str:
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
    return _asciidoc_table(
        ["Title", "Category", "Measure", "Scenarios"],
        rows,
    )


def _risk_table(records: list[ArchitectureRecord]) -> str:
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
    return _asciidoc_table(
        ["Title", "Severity", "Probability", "Mitigation", "Notes"],
        rows,
    )


def _glossary_table(records: list[ArchitectureRecord]) -> str:
    terms = _records_of_type(records, "glossary_term")
    rows = [
        [
            str(record.metadata.get("term", record.title)),
            str(record.metadata.get("definition", "")),
        ]
        for record in terms
    ]
    return _asciidoc_table(["Term", "Definition"], rows)


def _asciidoc_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return EMPTY_PLACEHOLDER
    cols = ",".join("1" for _ in headers)
    header_row = "|" + " |".join(headers)
    body_rows = ["|" + " |".join(row) for row in rows]
    return "\n".join(
        [
            f'[cols="{cols}", options="header"]',
            "|===",
            header_row,
            "",
            *body_rows,
            "|===",
        ]
    )


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
