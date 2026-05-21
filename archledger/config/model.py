from __future__ import annotations

import re
from dataclasses import dataclass, field

from archledger.errors import ConfigError
from archledger.model import CURRENT_SOURCE_SCHEMA_VERSION

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
        )
    )
)


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
class TrackingConfig:
    enabled: bool
    state_file: str
    scanner: str
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    max_file_bytes: int
    hash_algorithm: str


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    config_version: int
    archledger_dir: str
    project_uuid: str
    project_name: str
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
