from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ledgercore.errors import IdFormatError
from ledgercore.refs import parse_local_ref

from archledger.ids import (
    DEFAULT_ID_PREFIX,
    DEFAULT_ID_SEGMENT_MODE,
    DEFAULT_ID_WIDTH,
    LedgerIdFormat,
    format_ledger_id,
)
from archledger.record_types import (
    CLI_KIND_ALIASES as _CLI_KIND_ALIASES,
)
from archledger.record_types import (
    RECORD_TYPE_TO_DEFAULT_SECTION as _RECORD_TYPE_TO_DEFAULT_SECTION,
)
from archledger.record_types import (
    RECORD_TYPE_TO_DIR as _RECORD_TYPE_TO_DIR,
)
from archledger.record_types import (
    RECORD_TYPE_TO_TEMPLATE as _RECORD_TYPE_TO_TEMPLATE,
)
from archledger.record_types import RECORD_TYPES as _RECORD_TYPES
from archledger.record_types import (
    VALID_RECORD_TYPES as _VALID_RECORD_TYPES,
)

VALID_SOURCE_FORMATS = frozenset({"markdown", "asciidoc"})
VALID_BODY_FORMATS = VALID_SOURCE_FORMATS
SOURCE_FORMAT_EXTENSIONS = {
    "markdown": ".md",
    "asciidoc": ".adoc",
}
SOURCE_FORMAT_NATIVE_OUTPUTS = {
    "markdown": "markdown",
    "asciidoc": "asciidoc",
}
CURRENT_SOURCE_SCHEMA_VERSION = 3
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
    {"draft", "proposed", "accepted", "deprecated", "superseded", "archived"}
)
VISIBLE_BY_DEFAULT_STATUSES = frozenset({"proposed", "accepted", "deprecated"})
REQUIRED_RECORD_FIELDS = ("id", "kind", "type", "title", "status", "section", "order")
VALID_SOURCE_REF_ROLES = frozenset(
    {
        "implements",
        "validates",
        "documents",
        "configures",
        "migrates",
        "operates",
        "depends_on",
        "generates",
        "references",  # default / unspecified
    }
)
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
SECTION_BODY_PLACEHOLDERS = {
    "markdown": "<!-- archledger: add section-level prose here -->",
    "asciidoc": "// archledger: add section-level prose here",
}
EMPTY_SECTION_PLACEHOLDERS = {
    "markdown": "<!-- archledger: no accepted records for this section yet -->",
    "asciidoc": "// archledger: no accepted records for this section yet",
}


def known_source_extensions(
    config: object,
) -> tuple[str, ...]:
    """Return sorted tuple of all recognised source file extensions."""
    from archledger.config.model import ProjectConfig

    assert isinstance(config, ProjectConfig)
    return tuple(
        sorted(
            {
                *SOURCE_FORMAT_EXTENSIONS.values(),
                config.section_extension,
                config.record_extension,
            }
        )
    )


RECORD_TYPES = _RECORD_TYPES
CLI_KIND_ALIASES = _CLI_KIND_ALIASES
RECORD_TYPE_TO_DEFAULT_SECTION = _RECORD_TYPE_TO_DEFAULT_SECTION
RECORD_TYPE_TO_DIR = _RECORD_TYPE_TO_DIR
RECORD_TYPE_TO_TEMPLATE = _RECORD_TYPE_TO_TEMPLATE
VALID_RECORD_TYPES = _VALID_RECORD_TYPES

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


@dataclass(frozen=True, slots=True)
class SectionSpec:
    key: str
    title: str
    order: int
    number: int


MAJOR_SECTION_SPECS = (
    SectionSpec(
        key="introduction_and_goals",
        title="Introduction and Goals",
        order=10,
        number=1,
    ),
    SectionSpec(
        key="architecture_constraints",
        title="Architecture Constraints",
        order=20,
        number=2,
    ),
    SectionSpec(
        key="context_and_scope",
        title="Context and Scope",
        order=30,
        number=3,
    ),
    SectionSpec(
        key="solution_strategy",
        title="Solution Strategy",
        order=40,
        number=4,
    ),
    SectionSpec(
        key="building_block_view",
        title="Building Block View",
        order=50,
        number=5,
    ),
    SectionSpec(
        key="runtime_view",
        title="Runtime View",
        order=60,
        number=6,
    ),
    SectionSpec(
        key="deployment_view",
        title="Deployment View",
        order=70,
        number=7,
    ),
    SectionSpec(
        key="cross_cutting_concepts",
        title="Cross-cutting Concepts",
        order=80,
        number=8,
    ),
    SectionSpec(
        key="architecture_decisions",
        title="Architecture Decisions",
        order=90,
        number=9,
    ),
    SectionSpec(
        key="quality_requirements",
        title="Quality Requirements",
        order=100,
        number=10,
    ),
    SectionSpec(
        key="risks_and_technical_debt",
        title="Risks and Technical Debt",
        order=110,
        number=11,
    ),
    SectionSpec(
        key="glossary",
        title="Glossary",
        order=120,
        number=12,
    ),
)


@dataclass(frozen=True, slots=True)
class SourceRef:
    path: str
    symbols: tuple[str, ...]
    reason: str = ""
    role: str = ""


@dataclass(frozen=True, slots=True)
class ArchitectureRecord:
    id: str
    kind: str
    type: str
    title: str
    status: str
    section: str
    order: int
    path: Path
    metadata: dict[str, object]
    body: str
    source_refs: tuple[SourceRef, ...] = ()
    links: tuple = ()  # tuple[RecordLink, ...] — forward ref to links module
    test_refs: tuple = ()  # tuple[TestRef, ...] — forward ref to test_refs module
    scope: object = None  # RecordScope | None — forward ref to scopes module


def normalize_kind(kind: str) -> str:
    try:
        return CLI_KIND_ALIASES[kind.strip().lower().replace(" ", "_")]
    except KeyError as exc:
        raise ValueError(f"Unsupported record kind: {kind}") from exc


def validate_record(
    record: ArchitectureRecord,
    *,
    id_format: LedgerIdFormat | None = None,
    expected_segment: str | None = None,
    id_prefix: str = DEFAULT_ID_PREFIX,
    id_width: int = DEFAULT_ID_WIDTH,
) -> list[str]:
    resolved_format = (
        LedgerIdFormat(prefix=id_prefix, width=id_width)
        if id_format is None
        else id_format
    )
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
    if record.path.stem != record.id:
        issues.append(
            f"Record id {record.id!r} does not match filename stem {record.path.stem!r}"
        )
    try:
        parsed = parse_local_ref(record.id, width=id_width)
    except IdFormatError:
        issues.append(
            f"Record id {record.id!r} must be a local ID like <kind>-{id_width * '0'}."
        )
    else:
        if parsed.kind != record.kind:
            issues.append(
                f"Record id {record.id!r} has kind {parsed.kind!r}, "
                f"but metadata kind is {record.kind!r}."
            )
        if expected_segment is not None and parsed.kind != expected_segment:
            issues.append(
                f"Record id {record.id!r} has kind {parsed.kind!r}, "
                f"but {expected_segment!r} is expected for type {record.type!r}."
            )
    return issues


@dataclass(frozen=True, slots=True)
class SourceFormatSpec:
    """All per-format attributes for a source format."""

    extension: str
    native_output: str
    section_body_placeholder: str
    empty_section_placeholder: str


SOURCE_FORMAT_SPECS: dict[str, SourceFormatSpec] = {
    "markdown": SourceFormatSpec(
        extension=".md",
        native_output="markdown",
        section_body_placeholder="<!-- archledger: add section-level prose here -->",
        empty_section_placeholder=(
            "<!-- archledger: no accepted records for this section yet -->"
        ),
    ),
    "asciidoc": SourceFormatSpec(
        extension=".adoc",
        native_output="asciidoc",
        section_body_placeholder="// archledger: add section-level prose here",
        empty_section_placeholder=(
            "// archledger: no accepted records for this section yet"
        ),
    ),
}


def _lookup_source_format(
    specs: dict[str, SourceFormatSpec], source_format: str
) -> SourceFormatSpec:
    try:
        return specs[source_format]
    except KeyError as exc:
        raise ValueError(f"Unsupported source format: {source_format}") from exc


def source_format_spec(source_format: str) -> SourceFormatSpec:
    """Return the full spec for a source format."""
    return _lookup_source_format(SOURCE_FORMAT_SPECS, source_format)


def default_extension_for_source_format(source_format: str) -> str:
    return source_format_spec(source_format).extension


def native_output_format_for_source_format(source_format: str) -> str:
    return source_format_spec(source_format).native_output


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


def section_body_placeholder_for_source_format(source_format: str) -> str:
    return source_format_spec(source_format).section_body_placeholder


def empty_section_placeholder_for_source_format(source_format: str) -> str:
    return source_format_spec(source_format).empty_section_placeholder


def section_filename_for(
    section_spec: SectionSpec,
    extension: str = ".md",
    *,
    id_prefix: str = DEFAULT_ID_PREFIX,
    id_width: int = DEFAULT_ID_WIDTH,
    segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
    segment: str | None = None,
) -> str:
    return filename_for(
        section_spec.number,
        extension=extension,
        id_prefix=id_prefix,
        id_width=id_width,
        segment_mode=segment_mode,
        segment=segment,
    )


def filename_for(
    number: int,
    extension: str = ".md",
    *,
    id_prefix: str = DEFAULT_ID_PREFIX,
    id_width: int = DEFAULT_ID_WIDTH,
    segment_mode: str = DEFAULT_ID_SEGMENT_MODE,
    segment: str | None = None,
) -> str:
    record_id = format_ledger_id(
        number,
        prefix=id_prefix,
        width=id_width,
        segment_mode=segment_mode,
        segment=segment,
    )
    return f"{record_id}{extension}"


def id_from_filename(path: Path) -> str:
    return path.stem


def is_visible_status(
    status: str,
    *,
    include_draft: bool,
    include_superseded: bool,
    include_archived: bool = False,
) -> bool:
    if status == "draft":
        return include_draft
    if status == "superseded":
        return include_superseded
    if status == "archived":
        return include_archived
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
