"""Dataclasses for CLI option groups, extracted from cli.py init command."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class InitBuildOptions:
    """Build-related init options."""

    default_format: str | None = None
    default_output: str | None = None
    default_output_dir: str | None = None
    include_draft: bool = False
    include_superseded: bool = False
    strict: bool = False
    keep_intermediate: bool = False
    converter: str = "auto"
    pdf_engine: str = ""
    reference_docx: str = ""


@dataclass(frozen=True, slots=True)
class InitDiagramOptions:
    """Diagram-related init options."""

    enabled: bool = False
    renderer: str = "pass-through"
    default_type: str = "text"
    output_dir: str = "diagrams"
    image_format: str = "svg"
    kroki_url: str = ""


@dataclass(frozen=True, slots=True)
class InitArc42Options:
    """arc42 template init options."""

    title: str = "Architecture Documentation"
    language: str = "en"
    template_version: str = "9.0-EN"
    include_help: bool = False


@dataclass(frozen=True, slots=True)
class InitTrackingOptions:
    """Source tracking init options."""

    enabled: bool = True
    scanner: str = "auto"
    state_file: str = "source-state.json"
    max_file_bytes: int = 1_000_000
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InitOptions:
    """All init command options packaged as a single dataclass."""

    archledger_dir: str
    project_name: str | None = None
    project_uuid: str | None = None
    source_format: str = "asciidoc"
    id_prefix: str = "al"
    id_width: int = 4
    id_segment_mode: str = "none"
    profile: str = "arc42"
    extra_profiles: tuple[str, ...] = ()
    data_storage: str = "project"
    external_root: str | None = None
    build: InitBuildOptions = field(default_factory=InitBuildOptions)
    diagrams: InitDiagramOptions = field(default_factory=InitDiagramOptions)
    arc42: InitArc42Options = field(default_factory=InitArc42Options)
    tracking: InitTrackingOptions = field(default_factory=InitTrackingOptions)
