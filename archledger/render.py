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
class BuildResult:
    output_path: Path
    rendered_text: str


def build_document(
    repo: ArchitectureRepository,
    *,
    output: Path | None = None,
    include_draft: bool = False,
    include_superseded: bool = False,
    strict: bool = False,
) -> BuildResult:
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
    template = env.get_template("arc42_document.md.j2")
    rendered = template.render(
        title=repo.config.arc42_title,
        date=utc_now_iso()[:10],
        generator=f"archledger {__version__}",
        arc42_template_version=repo.config.arc42_template_version,
        section_body=lambda section_key: _section_body(sections, section_key),
        quality_goals_table=lambda: _quality_goals_table(records),
        stakeholders_table=lambda: _stakeholders_table(records),
        constraints_list=lambda: _constraints_list(records),
        context_interfaces=lambda context_kind: _context_interfaces(
            records,
            context_kind,
        ),
        building_block_view=lambda: _render_blocks(records),
        runtime_scenarios=lambda: _render_named_records(
            records,
            "runtime_scenario",
            "##",
        ),
        deployment_view=lambda: _render_named_records(
            records,
            "infrastructure",
            "##",
        ),
        concepts=lambda: _render_named_records(records, "concept", "##"),
        adrs=lambda: _render_named_records(records, "adr", "##"),
        quality_scenarios=lambda: _quality_scenarios(records),
        risks=lambda: _render_named_records(records, "risk", "##"),
        glossary_table=lambda: _glossary_table(records),
    )
    output_path = _resolve_output_path(repo, output)
    write_text(output_path, rendered)
    return BuildResult(output_path=output_path, rendered_text=rendered)


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


def _quality_goals_table(records: list[ArchitectureRecord]) -> str:
    quality_goals = _records_of_type(records, "quality_goal")
    rows = [
        [
            record.title,
            str(record.metadata.get("priority", "")),
            str(record.metadata.get("scenario", "")),
        ]
        for record in quality_goals
    ]
    return _markdown_table(["Title", "Priority", "Scenario"], rows)


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
    return _markdown_table(["Title", "Contact", "Expectations"], rows)


def _constraints_list(records: list[ArchitectureRecord]) -> str:
    constraints = _records_of_type(records, "constraint")
    if not constraints:
        return EMPTY_PLACEHOLDER
    chunks: list[str] = []
    for record in constraints:
        chunks.extend(
            [
                f"- **{record.title}**",
                f"  - Impact: {record.metadata.get('impact', '')}",
            ]
        )
        body = record.body.strip()
        if body:
            chunks.append(f"  - Notes: {body}")
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
        lines.append(f"- **{record.title}** -> {record.metadata.get('partner', '')}")
        body = record.body.strip()
        if body:
            lines.append(f"  - {body}")
    return "\n".join(lines)


def _render_blocks(records: list[ArchitectureRecord]) -> str:
    building_blocks = [
        record
        for record in records
        if record.type in {"white_box", "black_box", "interface"}
    ]
    if not building_blocks:
        return EMPTY_PLACEHOLDER

    lines: list[str] = []
    for record in sorted(building_blocks, key=record_sort_key):
        heading = "##" if record.type == "white_box" else "###"
        lines.extend([f"{heading} {record.title}", ""])
        body = record.body.strip() or EMPTY_PLACEHOLDER
        lines.append(body)
        if record.type == "black_box":
            interfaces = ", ".join(_string_list(record.metadata.get("interfaces")))
            locations = ", ".join(_string_list(record.metadata.get("location")))
            requirements = ", ".join(
                _string_list(record.metadata.get("fulfilled_requirements"))
            )
            risks = ", ".join(_string_list(record.metadata.get("risks")))
            lines.extend(
                [
                    "",
                    f"**Interfaces:** {interfaces}",
                    f"**Location:** {locations}",
                    f"**Fulfilled requirements:** {requirements}",
                    f"**Risks:** {risks}",
                ]
            )
        if record.type == "interface":
            lines.extend(
                [
                    "",
                    f"**Protocol:** {record.metadata.get('protocol', '')}",
                ]
            )
        lines.append("")
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
    return _markdown_table(
        ["Title", "Quality", "Stimulus", "Response measure"],
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
    return _markdown_table(["Term", "Definition"], rows)


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return EMPTY_PLACEHOLDER
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body_rows = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_row, separator, *body_rows])


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
