from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

VALID_SOURCE_FORMATS = frozenset({"markdown", "asciidoc"})
SOURCE_FORMAT_EXTENSIONS = {
    "markdown": ".md",
    "asciidoc": ".adoc",
}
VALID_OUTPUT_FORMATS = frozenset(
    {"asciidoc", "html", "pdf", "docx", "markdown", "rst", "textile"}
)
OUTPUT_FORMAT_EXTENSIONS = {
    "asciidoc": ".adoc",
    "html": ".html",
    "pdf": ".pdf",
    "docx": ".docx",
    "markdown": ".md",
    "rst": ".rst",
    "textile": ".textile",
}
VALID_STATUSES = frozenset(
    {"draft", "proposed", "accepted", "deprecated", "superseded"}
)
VISIBLE_BY_DEFAULT_STATUSES = frozenset({"proposed", "accepted", "deprecated"})
REQUIRED_RECORD_FIELDS = ("id", "type", "title", "status", "section", "order")
PLACEHOLDER_SNIPPETS = (
    "Describe this requirement.",
    "Describe the purpose and responsibility of this black box.",
    "Explain the decomposition.",
    "Explain this strategy item.",
    "Describe the forces and problem.",
    "Describe the decision.",
    "Describe positive and negative consequences.",
    "Alternative: reason rejected.",
    "Explain the architecture concept.",
    "Describe the quality scenario.",
    "Describe this quality requirement.",
    "Describe the runtime scenario.",
    "Describe the deployment or infrastructure view.",
)

SECTION_ORDER = {
    "introduction_and_goals": 10,
    "requirements_overview": 20,
    "architecture_constraints": 30,
    "context_and_scope": 40,
    "solution_strategy": 50,
    "building_block_view": 60,
    "runtime_view": 70,
    "deployment_view": 80,
    "cross_cutting_concepts": 90,
    "architecture_decisions": 100,
    "quality_requirements": 110,
    "risks_and_technical_debt": 120,
    "glossary": 130,
}

RECORD_TYPE_TO_DIR = {
    "requirement": "requirements",
    "stakeholder": "stakeholders",
    "quality_goal": "quality_goals",
    "constraint": "constraints",
    "context_interface": "contexts",
    "strategy_item": "strategy",
    "white_box": "building_blocks",
    "black_box": "building_blocks",
    "interface": "building_blocks",
    "runtime_scenario": "runtime",
    "infrastructure": "deployment",
    "concept": "concepts",
    "adr": "decisions",
    "quality_requirement": "quality_requirements",
    "quality_scenario": "quality_scenarios",
    "risk": "risks",
    "glossary_term": "glossary",
}

RECORD_TYPE_TO_FILENAME_PREFIX = {
    "requirement": "requirement",
    "stakeholder": "stakeholder",
    "quality_goal": "quality_goal",
    "constraint": "constraint",
    "context_interface": "context_interface",
    "strategy_item": "strategy_item",
    "white_box": "white_box",
    "black_box": "black_box",
    "interface": "interface",
    "runtime_scenario": "runtime",
    "infrastructure": "infrastructure",
    "concept": "concept",
    "adr": "adr",
    "quality_requirement": "quality_requirement",
    "quality_scenario": "quality_scenario",
    "risk": "risk",
    "glossary_term": "glossary",
}

RECORD_TYPE_TO_DEFAULT_SECTION = {
    "requirement": "introduction_and_goals",
    "stakeholder": "introduction_and_goals",
    "quality_goal": "introduction_and_goals",
    "constraint": "architecture_constraints",
    "context_interface": "context_and_scope",
    "strategy_item": "solution_strategy",
    "white_box": "building_block_view",
    "black_box": "building_block_view",
    "interface": "building_block_view",
    "runtime_scenario": "runtime_view",
    "infrastructure": "deployment_view",
    "concept": "cross_cutting_concepts",
    "adr": "architecture_decisions",
    "quality_requirement": "quality_requirements",
    "quality_scenario": "quality_requirements",
    "risk": "risks_and_technical_debt",
    "glossary_term": "glossary",
}

VALID_RECORD_TYPES = frozenset(RECORD_TYPE_TO_DIR)
RECORD_TYPE_TO_TEMPLATE = {
    "requirement": "requirement.md.j2",
    "stakeholder": "stakeholder.md.j2",
    "quality_goal": "quality_goal.md.j2",
    "constraint": "constraint.md.j2",
    "context_interface": "context_interface.md.j2",
    "strategy_item": "strategy_item.md.j2",
    "white_box": "white_box.md.j2",
    "black_box": "black_box.md.j2",
    "interface": "interface.md.j2",
    "runtime_scenario": "runtime_scenario.md.j2",
    "infrastructure": "infrastructure.md.j2",
    "concept": "concept.md.j2",
    "adr": "adr.md.j2",
    "quality_requirement": "quality_requirement.md.j2",
    "quality_scenario": "quality_scenario.md.j2",
    "risk": "risk.md.j2",
    "glossary_term": "glossary_term.md.j2",
}

CLI_KIND_ALIASES = {
    "requirement": "requirement",
    "stakeholder": "stakeholder",
    "quality-goal": "quality_goal",
    "quality_goal": "quality_goal",
    "constraint": "constraint",
    "context-interface": "context_interface",
    "context_interface": "context_interface",
    "strategy-item": "strategy_item",
    "strategy_item": "strategy_item",
    "white-box": "white_box",
    "white_box": "white_box",
    "black-box": "black_box",
    "black_box": "black_box",
    "interface": "interface",
    "runtime": "runtime_scenario",
    "runtime_scenario": "runtime_scenario",
    "infrastructure": "infrastructure",
    "concept": "concept",
    "adr": "adr",
    "quality-requirement": "quality_requirement",
    "quality_requirement": "quality_requirement",
    "quality-scenario": "quality_scenario",
    "quality_scenario": "quality_scenario",
    "risk": "risk",
    "glossary-term": "glossary_term",
    "glossary_term": "glossary_term",
}


@dataclass(frozen=True, slots=True)
class SectionSpec:
    key: str
    title: str
    order: int
    filename: str


MAJOR_SECTION_SPECS = (
    SectionSpec(
        key="introduction_and_goals",
        title="Introduction and Goals",
        order=10,
        filename="01_introduction_and_goals.md",
    ),
    SectionSpec(
        key="architecture_constraints",
        title="Architecture Constraints",
        order=20,
        filename="02_architecture_constraints.md",
    ),
    SectionSpec(
        key="context_and_scope",
        title="Context and Scope",
        order=30,
        filename="03_context_and_scope.md",
    ),
    SectionSpec(
        key="solution_strategy",
        title="Solution Strategy",
        order=40,
        filename="04_solution_strategy.md",
    ),
    SectionSpec(
        key="building_block_view",
        title="Building Block View",
        order=50,
        filename="05_building_block_view.md",
    ),
    SectionSpec(
        key="runtime_view",
        title="Runtime View",
        order=60,
        filename="06_runtime_view.md",
    ),
    SectionSpec(
        key="deployment_view",
        title="Deployment View",
        order=70,
        filename="07_deployment_view.md",
    ),
    SectionSpec(
        key="cross_cutting_concepts",
        title="Cross-cutting Concepts",
        order=80,
        filename="08_cross_cutting_concepts.md",
    ),
    SectionSpec(
        key="architecture_decisions",
        title="Architecture Decisions",
        order=90,
        filename="09_architecture_decisions.md",
    ),
    SectionSpec(
        key="quality_requirements",
        title="Quality Requirements",
        order=100,
        filename="10_quality_requirements.md",
    ),
    SectionSpec(
        key="risks_and_technical_debt",
        title="Risks and Technical Debt",
        order=110,
        filename="11_risks_and_technical_debt.md",
    ),
    SectionSpec(
        key="glossary",
        title="Glossary",
        order=120,
        filename="12_glossary.md",
    ),
)


@dataclass(frozen=True, slots=True)
class ArchitectureRecord:
    id: str
    type: str
    title: str
    status: str
    section: str
    order: int
    path: Path
    metadata: dict[str, object]
    body: str


def normalize_kind(kind: str) -> str:
    try:
        return CLI_KIND_ALIASES[kind.strip().lower().replace(" ", "_")]
    except KeyError as exc:
        raise ValueError(f"Unsupported record kind: {kind}") from exc


def validate_record(record: ArchitectureRecord) -> list[str]:
    issues: list[str] = []
    if record.type not in VALID_RECORD_TYPES and record.type != "section":
        issues.append(f"Unknown record type: {record.type}")
    if record.status not in VALID_STATUSES:
        issues.append(f"Unknown status: {record.status}")
    if record.section not in SECTION_ORDER:
        issues.append(f"Unknown section: {record.section}")
    if isinstance(record.order, bool) or not isinstance(record.order, int):
        issues.append("Order must be an integer")
    if not record.title.strip():
        issues.append("Title must not be empty")
    if record.type != "section" and record.path.stem != record.id:
        issues.append(
            f"Record id {record.id!r} does not match filename stem {record.path.stem!r}"
        )
    return issues


def default_extension_for_source_format(source_format: str) -> str:
    try:
        return SOURCE_FORMAT_EXTENSIONS[source_format]
    except KeyError as exc:
        raise ValueError(f"Unsupported source format: {source_format}") from exc


def infer_output_format_from_path(path: str | Path) -> str | None:
    suffix = Path(path).suffix.lower()
    for output_format, extension in OUTPUT_FORMAT_EXTENSIONS.items():
        if extension == suffix:
            return output_format
    return None


def default_document_filename_for_output_format(output_format: str) -> str:
    try:
        extension = OUTPUT_FORMAT_EXTENSIONS[output_format]
    except KeyError as exc:
        raise ValueError(f"Unsupported output format: {output_format}") from exc
    return f"architecture{extension}"


def document_template_name_for_source_format(source_format: str) -> str:
    if source_format not in VALID_SOURCE_FORMATS:
        raise ValueError(f"Unsupported source format: {source_format}")
    return f"arc42_document{default_extension_for_source_format(source_format)}.j2"


def record_template_name_for_source_format(
    kind: str,
    source_format: str = "markdown",
) -> str:
    normalized_kind = normalize_kind(kind)
    template_name = RECORD_TYPE_TO_TEMPLATE[normalized_kind]
    if source_format == "markdown":
        return template_name
    if source_format == "asciidoc":
        return template_name.replace(".md.j2", ".adoc.j2")
    raise ValueError(f"Unsupported source format: {source_format}")


def section_filename_for(section_spec: SectionSpec, extension: str = ".md") -> str:
    return f"{Path(section_spec.filename).stem}{extension}"


def filename_for(kind: str, number: int, extension: str = ".md") -> str:
    normalized_kind = normalize_kind(kind)
    prefix = RECORD_TYPE_TO_FILENAME_PREFIX[normalized_kind]
    if prefix == "adr":
        return f"adr{number:04d}{extension}"
    return f"{prefix}_{number:04d}{extension}"


def id_from_filename(path: Path) -> str:
    return path.stem


def is_visible_status(
    status: str,
    *,
    include_draft: bool,
    include_superseded: bool,
) -> bool:
    if status == "draft":
        return include_draft
    if status == "superseded":
        return include_superseded
    return status in VISIBLE_BY_DEFAULT_STATUSES


def record_sort_key(record: ArchitectureRecord) -> tuple[int, int, str, int, str]:
    level_value = record.metadata.get("level", 0)
    level = (
        level_value
        if isinstance(level_value, int) and not isinstance(level_value, bool)
        else 0
    )
    parent_value = record.metadata.get("parent")
    parent = "" if parent_value in (None, "", "null") else str(parent_value)
    return (
        SECTION_ORDER.get(record.section, 9999),
        level,
        parent,
        record.order,
        record.id,
    )
