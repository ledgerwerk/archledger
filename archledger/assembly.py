from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from archledger import __version__
from archledger.dialects import get_dialect
from archledger.errors import RenderError
from archledger.model import (
    ArchitectureRecord,
    default_document_filename_for_output_format,
    document_template_name_for_source_format,
    is_visible_status,
    native_output_format_for_source_format,
)
from archledger.repository import ArchitectureRepository
from archledger.section_rendering import (
    adr_sections,
    building_block_hierarchy,
    concepts,
    constraints_list,
    context_interfaces,
    deployment_view,
    glossary_table,
    quality_goals_table,
    quality_requirements_overview,
    quality_scenarios,
    requirements_overview,
    risk_table,
    runtime_scenarios,
    section_body,
    section_diagrams,
    solution_strategy_items,
    stakeholders_table,
)
from archledger.storage.common import utc_now_iso, write_text


@dataclass(frozen=True, slots=True)
class AssemblyResult:
    output_path: Path
    rendered_text: str
    source_format: str


def assemble_document(
    repo: ArchitectureRepository,
    *,
    output: Path | None = None,
    source_format: str | None = None,
    include_draft: bool = False,
    include_superseded: bool = False,
    strict: bool = False,
    write: bool = True,
) -> AssemblyResult:
    check_result = repo.check(strict=strict)
    if check_result.has_failures(strict=strict):
        raise RenderError(
            f"Build blocked by {len(check_result.errors)} error(s) and "
            f"{len(check_result.warnings)} warning(s)."
        )

    resolved_source_format = (
        repo.config.source_format if source_format is None else source_format
    )
    dialect = get_dialect(resolved_source_format)
    all_records = repo.load_all_records(include_sections=True)
    sections = {
        record.section: record for record in all_records if record.type == "section"
    }
    records = _visible_records(
        all_records,
        include_draft=include_draft,
        include_superseded=include_superseded,
    )
    env = Environment(
        loader=PackageLoader("archledger", "templates"),
        autoescape=select_autoescape(
            enabled_extensions=(),
            default_for_string=False,
        ),
        keep_trailing_newline=True,
    )
    template = env.get_template(
        document_template_name_for_source_format(resolved_source_format)
    )
    rendered = template.render(
        title=repo.config.arc42_title,
        date=_document_date(records),
        generator=f"archledger {__version__}",
        arc42_template_version=repo.config.arc42_template_version,
        section_body=lambda section_key: section_body(sections, section_key, dialect),
        requirements_overview=lambda: requirements_overview(records, dialect),
        quality_goals_table=lambda: quality_goals_table(records, dialect),
        stakeholders_table=lambda: stakeholders_table(records, dialect),
        constraints_list=lambda: constraints_list(records, dialect),
        context_interfaces=lambda context_kind: context_interfaces(
            records,
            context_kind,
            dialect,
        ),
        solution_strategy_items=lambda: solution_strategy_items(records, dialect),
        section_diagrams=lambda section_key: section_diagrams(
            records,
            section_key,
            dialect,
        ),
        building_block_hierarchy=lambda: building_block_hierarchy(records, dialect),
        runtime_scenarios=lambda: runtime_scenarios(records, dialect),
        deployment_view=lambda: deployment_view(records, dialect),
        concepts=lambda: concepts(records, dialect),
        adr_sections=lambda: adr_sections(records, dialect),
        quality_requirements_overview=lambda: quality_requirements_overview(
            records,
            dialect,
        ),
        quality_scenarios=lambda: quality_scenarios(records, dialect),
        risk_table=lambda: risk_table(records, dialect),
        glossary_table=lambda: glossary_table(records, dialect),
    )
    output_path = _resolve_output_path(repo, resolved_source_format, output)
    if write:
        write_text(output_path, rendered)
    return AssemblyResult(
        output_path=output_path,
        rendered_text=rendered,
        source_format=resolved_source_format,
    )


def _document_date(records: list[ArchitectureRecord]) -> str:
    source_date_epoch = os.getenv("SOURCE_DATE_EPOCH")
    if source_date_epoch:
        try:
            timestamp = int(source_date_epoch)
        except ValueError as exc:
            raise RenderError(
                "SOURCE_DATE_EPOCH must be an integer Unix timestamp."
            ) from exc
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()

    latest_date: date | None = None
    for record in records:
        for key in ("updated_at", "date"):
            metadata_value = record.metadata.get(key)
            parsed = _parse_record_datetime(metadata_value)
            if parsed is None:
                continue
            candidate = parsed.date()
            if latest_date is None or candidate > latest_date:
                latest_date = candidate

    if latest_date is not None:
        return latest_date.isoformat()
    return utc_now_iso()[:10]


def _parse_record_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if len(candidate) == 10:
        try:
            return datetime.strptime(candidate, "%Y-%m-%d")
        except ValueError:
            return None

    normalized = candidate
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def assemble_asciidoc_document(
    repo: ArchitectureRepository,
    *,
    output: Path | None = None,
    include_draft: bool = False,
    include_superseded: bool = False,
    strict: bool = False,
    write: bool = True,
) -> AssemblyResult:
    return assemble_document(
        repo,
        output=output,
        source_format="asciidoc",
        include_draft=include_draft,
        include_superseded=include_superseded,
        strict=strict,
        write=write,
    )


def _visible_records(
    all_records: list[ArchitectureRecord],
    *,
    include_draft: bool,
    include_superseded: bool,
) -> list[ArchitectureRecord]:
    return [
        record
        for record in all_records
        if record.type != "section"
        and is_visible_status(
            record.status,
            include_draft=include_draft,
            include_superseded=include_superseded,
        )
    ]


def _resolve_output_path(
    repo: ArchitectureRepository,
    source_format: str,
    output: Path | None,
) -> Path:
    if output is None:
        native_output_format = native_output_format_for_source_format(source_format)
        default_output = (
            repo.config.build_default_output
            if repo.config.build_default_format == native_output_format
            else default_document_filename_for_output_format(native_output_format)
        )
        return repo.paths.build_dir / default_output
    if output.is_absolute():
        return output
    return repo.paths.workspace_root / output
