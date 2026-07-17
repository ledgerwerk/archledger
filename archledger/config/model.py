from __future__ import annotations

import re
from dataclasses import dataclass, field
from uuid import UUID

from archledger.errors import ConfigError
from archledger.ids import (
    DEFAULT_ID_PREFIX,
    DEFAULT_ID_SEGMENT_MODE,
    DEFAULT_ID_WIDTH,
    LedgerIdFormat,
)
from archledger.model import CURRENT_SOURCE_SCHEMA_VERSION

# --- Public allowed-value constants ---
# Shared by parse.py, render.py, and cli.py.
VALID_PROFILES: frozenset[str] = frozenset({"arc42"})
VALID_PROFILE_KINDS: frozenset[str] = frozenset({"documentation"})
VALID_BUILD_CONVERTERS: frozenset[str] = frozenset({"auto", "pandoc", "asciidoctor"})
VALID_TRACKING_SCANNERS: frozenset[str] = frozenset({"auto", "git", "filesystem"})
VALID_TRACKING_HASH_ALGORITHMS: frozenset[str] = frozenset({"sha256"})
VALID_DIAGRAM_RENDERERS: frozenset[str] = frozenset(
    {"pass-through", "mermaid-cli", "asciidoctor-diagram"}
)
VALID_DIAGRAM_TYPES: frozenset[str] = frozenset(
    {"text", "ascii", "unicode", "svgbob", "mermaid"}
)
VALID_DIAGRAM_IMAGE_FORMATS: frozenset[str] = frozenset({"svg", "png"})

# Default arc42 sections directory, relative to archledger_dir.
DEFAULT_ARC42_SECTIONS_DIR = "profiles/arc42/sections"
DEFAULT_TRACKING_INCLUDE = (
    "**/*.py",
    "**/*.toml",
    "**/*.md",
    "**/*.adoc",
    "**/*.rst",
    "**/*.j2",
    "**/*.yaml",
    "**/*.yml",
    "**/*.json",
)
DEFAULT_TRACKING_EXCLUDE = tuple(
    dict.fromkeys(
        (
            ".git/**",
            ".venv/**",
            "**/__pycache__/**",
            ".mypy_cache/**",
            ".pytest_cache/**",
            ".ruff_cache/**",
            "dist/**",
            "build/**",
            ".ledger/**",
        )
    )
)

DEFAULT_LEDGER_CODE = "al"
DEFAULT_LEDGER_NAME = "archledger"
DEFAULT_ID_KIND = "content"
DEFAULT_ID_KIND_MAP: dict[str, str] = {
    "section": "content",
    "requirement": "content",
    "acceptance_criterion": "ac",
    "stakeholder": "content",
    "quality_goal": "quality",
    "constraint": "constraint",
    "context_interface": "context",
    "strategy_item": "strategy",
    "white_box": "block",
    "black_box": "block",
    "interface": "block",
    "runtime_scenario": "runtime",
    "infrastructure": "deploy",
    "concept": "concept",
    "adr": "adr",
    "quality_requirement": "quality",
    "quality_scenario": "quality",
    "risk": "risk",
    "diagram": "diagram",
    "glossary_term": "glossary",
    "archive_tombstone": "archive",
}
DEFAULT_ID_SEGMENT = DEFAULT_ID_KIND
DEFAULT_ID_SEGMENT_MAP = DEFAULT_ID_KIND_MAP


@dataclass(frozen=True, slots=True)
class LedgerConfig:
    code: str
    name: str


@dataclass(frozen=True, slots=True)
class SourceConfig:
    format: str
    schema_version: int
    front_matter: str
    section_extension: str
    record_extension: str


@dataclass(frozen=True, slots=True)
class BuildOutputConfig:
    enabled: bool | None = None
    tool: str | None = None
    pdf_engine: str = ""
    reference_docx: str = ""


@dataclass(frozen=True, slots=True)
class BuildConfig:
    default_output: str
    default_format: str
    default_output_dir: str
    include_draft: bool
    include_superseded: bool
    strict: bool
    keep_intermediate: bool
    converter: str
    pdf_engine: str
    reference_docx: str
    outputs: dict[str, BuildOutputConfig]


@dataclass(frozen=True, slots=True)
class Arc42Config:
    template_version: str
    language: str
    title: str
    include_help: bool


@dataclass(frozen=True, slots=True)
class SkillConfig:
    installed: bool
    path: str


@dataclass(frozen=True, slots=True)
class IdConfig:
    prefix: str
    width: int
    segment_mode: str
    default_segment: str
    segment_map: dict[str, str]
    default_kind: str
    kind_map: dict[str, str]


@dataclass(frozen=True, slots=True)
class ProfilesConfig:
    """Top-level profile selection: which profiles are enabled."""

    enabled: tuple[str, ...] = ("arc42",)
    default: str = "arc42"


@dataclass(frozen=True, slots=True)
class Arc42ProfileConfig:
    """arc42 documentation profile settings."""

    kind: str = "documentation"
    template: str = "arc42"
    sections_dir: str = DEFAULT_ARC42_SECTIONS_DIR
    build_template: str = "arc42_document"
    include_help: bool = False


@dataclass(frozen=True, slots=True)
class ProjectProfilesConfig:
    """Aggregated profile configuration for a project."""

    profiles: ProfilesConfig = ProfilesConfig()
    arc42: Arc42ProfileConfig = Arc42ProfileConfig()


@dataclass(frozen=True, slots=True)
class TrackingConfig:
    enabled: bool
    state_file: str
    scanner: str
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    max_file_bytes: int
    hash_algorithm: str


@dataclass(frozen=True, slots=True)
class DiagramConfig:
    enabled: bool
    renderer: str
    default_type: str
    output_dir: str
    image_format: str
    kroki_url: str


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Archledger tool configuration (currently version 11, migrating to 12).

    Runtime identity fields (archledger_dir, project_uuid, project_name) are
    removed from serialized config in version 12 and supplied by the project
    context at runtime. They default to empty strings for backward compat.
    """

    config_version: int
    archledger_dir: str = ""
    project_uuid: str = ""
    project_name: str = ""
    ledger_code: str = DEFAULT_LEDGER_CODE
    id_width: int = DEFAULT_ID_WIDTH
    id_default_kind: str = DEFAULT_ID_KIND
    id_kind_map: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_ID_KIND_MAP)
    )

    # Deprecated legacy fields retained for compatibility.
    id_prefix: str = DEFAULT_ID_PREFIX
    id_segment_mode: str = DEFAULT_ID_SEGMENT_MODE
    id_default_segment: str = DEFAULT_ID_KIND
    id_segment_map: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_ID_KIND_MAP)
    )
    source_format: str = "markdown"
    source_schema_version: int = CURRENT_SOURCE_SCHEMA_VERSION
    front_matter: str = "yaml"
    section_extension: str = ".md"
    record_extension: str = ".md"
    build_default_output: str = "architecture.md"
    build_default_format: str = "markdown"
    build_output_dir: str = "build"
    build_include_draft: bool = False
    build_include_superseded: bool = False
    build_strict: bool = False
    build_keep_intermediate: bool = False
    build_converter: str = "auto"
    build_pdf_engine: str = ""
    build_reference_docx: str = ""
    build_outputs: dict[str, dict[str, object]] = field(default_factory=dict)
    arc42_template_version: str = "9.0-EN"
    arc42_language: str = "en"
    arc42_title: str = "Architecture Documentation"
    arc42_include_help: bool = False
    skill_installed: bool = False
    skill_path: str = "skills/archledger/SKILL.md"
    tracking_enabled: bool = True
    tracking_state_file: str = "source-state.json"
    tracking_scanner: str = "auto"
    tracking_include: tuple[str, ...] = DEFAULT_TRACKING_INCLUDE
    tracking_exclude: tuple[str, ...] = DEFAULT_TRACKING_EXCLUDE
    tracking_max_file_bytes: int = 1_000_000
    tracking_hash_algorithm: str = "sha256"
    diagram_enabled: bool = False
    diagram_renderer: str = "pass-through"
    diagram_default_type: str = "text"
    diagram_output_dir: str = "diagrams"
    diagram_image_format: str = "svg"
    diagram_kroki_url: str = ""
    profiles: ProjectProfilesConfig = field(default_factory=ProjectProfilesConfig)
    profiles_present: bool = False
    legacy_sections_warned: bool = False

    @property
    def ledger_name(self) -> str:
        """Deprecated: use project_name from context instead."""
        return self.project_name or DEFAULT_LEDGER_NAME

    @property
    def profile(self) -> str:
        """Return the default profile name (back-compat accessor)."""
        return self.profiles.profiles.default

    @property
    def ledger(self) -> LedgerConfig:
        return LedgerConfig(code=self.ledger_code, name=self.ledger_name)

    @property
    def source(self) -> SourceConfig:
        return SourceConfig(
            format=self.source_format,
            schema_version=self.source_schema_version,
            front_matter=self.front_matter,
            section_extension=self.section_extension,
            record_extension=self.record_extension,
        )

    @property
    def build(self) -> BuildConfig:
        return BuildConfig(
            default_output=self.build_default_output,
            default_format=self.build_default_format,
            default_output_dir=self.build_output_dir,
            include_draft=self.build_include_draft,
            include_superseded=self.build_include_superseded,
            strict=self.build_strict,
            keep_intermediate=self.build_keep_intermediate,
            converter=self.build_converter,
            pdf_engine=self.build_pdf_engine,
            reference_docx=self.build_reference_docx,
            outputs={
                name: _build_output_config(value)
                for name, value in self.build_outputs.items()
            },
        )

    @property
    def arc42(self) -> Arc42Config:
        return Arc42Config(
            template_version=self.arc42_template_version,
            language=self.arc42_language,
            title=self.arc42_title,
            include_help=self.arc42_include_help,
        )

    @property
    def skill(self) -> SkillConfig:
        return SkillConfig(
            installed=self.skill_installed,
            path=self.skill_path,
        )

    @property
    def ids(self) -> IdConfig:
        return IdConfig(
            prefix=self.id_prefix,
            width=self.id_width,
            segment_mode=self.id_segment_mode,
            default_segment=self.id_default_segment,
            segment_map=dict(self.id_segment_map),
            default_kind=self.id_default_kind,
            kind_map=dict(self.id_kind_map),
        )

    @property
    def id_format(self) -> LedgerIdFormat:
        return LedgerIdFormat(
            prefix=self.id_prefix,
            width=self.id_width,
            segment_mode=self.id_segment_mode,
        )

    @property
    def tracking(self) -> TrackingConfig:
        return TrackingConfig(
            enabled=self.tracking_enabled,
            state_file=self.tracking_state_file,
            scanner=self.tracking_scanner,
            include=self.tracking_include,
            exclude=self.tracking_exclude,
            max_file_bytes=self.tracking_max_file_bytes,
            hash_algorithm=self.tracking_hash_algorithm,
        )

    @property
    def diagrams(self) -> DiagramConfig:
        return DiagramConfig(
            enabled=self.diagram_enabled,
            renderer=self.diagram_renderer,
            default_type=self.diagram_default_type,
            output_dir=self.diagram_output_dir,
            image_format=self.diagram_image_format,
            kroki_url=self.diagram_kroki_url,
        )

    def profiles_config(self) -> ProjectProfilesConfig:
        """Return the structured profiles configuration."""
        return self.profiles


def normalize_project_name(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", name.strip().lower()).strip("-")
    if not normalized:
        raise ConfigError("Project name must contain at least one letter or number.")
    return normalized


def _build_output_config(value: dict[str, object]) -> BuildOutputConfig:
    enabled_value = value.get("enabled")
    tool_value = value.get("tool")
    pdf_engine_value = value.get("pdf_engine")
    reference_docx_value = value.get("reference_docx")
    return BuildOutputConfig(
        enabled=enabled_value if isinstance(enabled_value, bool) else None,
        tool=tool_value if isinstance(tool_value, str) else None,
        pdf_engine=pdf_engine_value if isinstance(pdf_engine_value, str) else "",
        reference_docx=(
            reference_docx_value if isinstance(reference_docx_value, str) else ""
        ),
    )


def validate_uuid(value: str) -> str:
    """Validate and normalise a UUID string."""
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ConfigError("project_uuid must be a valid UUID.") from exc
