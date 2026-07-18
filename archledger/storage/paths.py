from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ledgercore.paths import is_relative_to as core_is_relative_to

from archledger.errors import ConfigError
from archledger.storage.project_config import ProjectConfig

CANONICAL_PROJECT_CONFIG_FILENAME = "ledger.toml"
HIDDEN_PROJECT_CONFIG_FILENAME = "ledger.local.toml"
PROJECT_CONFIG_FILENAMES = (CANONICAL_PROJECT_CONFIG_FILENAME,)
DEFAULT_ARCHLEDGER_DIR_NAME = ".ledger/arch/archledger"


def is_relative_to(path: Path, parent: Path) -> bool:
    return core_is_relative_to(path, parent)


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    workspace_root: Path
    config_root: Path
    manifest_path: Path
    local_config_path: Path
    config_path: Path
    archledger_dir: Path
    sections_dir: Path
    records_dir: Path
    archive_dir: Path
    build_dir: Path
    storage_meta_path: Path
    source_state_path: Path
    document_state_path: Path
    mount_name: str = "data"
    mount_storage: str = "repository"
    mount_scope: str | None = None
    mount_source: str = "repository"


def discover_project_config(start: Path) -> tuple[Path, list[str]]:
    """Discover the canonical shared manifest for compatibility callers."""
    from archledger.ledgercore_backend import locate_ledger_project

    locator = locate_ledger_project(
        start,
        legacy_tool_filenames=("archledger.toml", ".archledger.toml"),
    )
    if locator is None:
        raise ConfigError(
            "No .ledger/ledger.toml found. Run: archledger init",
            details={"code": "ARCHLEDGER_PROJECT_NOT_FOUND"},
        )
    if locator.is_legacy:
        raise ConfigError(
            "Legacy Archledger layout found. Run: archledger migrate project",
            details={"code": "ARCHLEDGER_MIGRATION_REQUIRED"},
        )
    return locator.manifest_path, []


def resolve_project_paths(start: Path) -> tuple[ProjectPaths, ProjectConfig, list[str]]:
    """Resolve paths through Ledgercore's canonical project context.

    For test/development convenience, auto-initializes a schema-3 project
    when a legacy archledger.toml/.archledger.toml exists without a manifest.
    """
    from archledger.project_context import load_project_context

    # If no manifest exists but legacy config does, auto-init for compatibility.
    manifest_path = start / ".ledger" / "ledger.toml"
    if not manifest_path.is_file():
        legacy_configs = [
            start / "archledger.toml",
            start / ".archledger.toml",
        ]
        if any(p.is_file() for p in legacy_configs):
            from archledger.cli_options import (
                InitArc42Options,
                InitBuildOptions,
                InitDiagramOptions,
                InitOptions,
                InitTrackingOptions,
            )
            from archledger.config.parse import load_project_config
            from archledger.project_init import initialize_project

            legacy_path = next(p for p in legacy_configs if p.is_file())
            legacy_config = load_project_config(legacy_path)
            init_opts = InitOptions(
                archledger_dir="data",
                project_name=legacy_config.project_name or start.name,
                project_uuid=legacy_config.project_uuid or None,
                source_format=legacy_config.source_format,
                id_prefix=legacy_config.id_prefix,
                id_width=legacy_config.id_width,
                id_segment_mode=legacy_config.id_segment_mode,
                profile="arc42",
                data_storage="project",
                external_root=None,
                build=InitBuildOptions(
                    default_format=legacy_config.build_default_format,
                    default_output=legacy_config.build_default_output,
                    default_output_dir=legacy_config.build_output_dir,
                    include_draft=legacy_config.build_include_draft,
                    include_superseded=legacy_config.build_include_superseded,
                    strict=legacy_config.build_strict,
                    keep_intermediate=legacy_config.build_keep_intermediate,
                    converter=legacy_config.build_converter,
                    pdf_engine=legacy_config.build_pdf_engine,
                    reference_docx=legacy_config.build_reference_docx,
                ),
                diagrams=InitDiagramOptions(
                    enabled=legacy_config.diagram_enabled,
                    renderer=legacy_config.diagram_renderer,
                    default_type=legacy_config.diagram_default_type,
                    output_dir=legacy_config.diagram_output_dir,
                    image_format=legacy_config.diagram_image_format,
                    kroki_url=legacy_config.diagram_kroki_url,
                ),
                arc42=InitArc42Options(
                    title=legacy_config.arc42_title,
                    language=legacy_config.arc42_language,
                    template_version=legacy_config.arc42_template_version,
                    include_help=legacy_config.arc42_include_help,
                ),
                tracking=InitTrackingOptions(
                    enabled=legacy_config.tracking_enabled,
                    scanner=legacy_config.tracking_scanner,
                    state_file=legacy_config.tracking_state_file,
                    max_file_bytes=legacy_config.tracking_max_file_bytes,
                    include=legacy_config.tracking_include or (),
                    exclude=legacy_config.tracking_exclude or (),
                ),
            )
            initialize_project(start, init_opts)

    context = load_project_context(start)
    if not isinstance(context.config, ProjectConfig):
        raise ConfigError("Canonical Archledger configuration is invalid.")
    config = context.config
    # Propagate project identity from manifest to config (not in file for v12+).
    if not config.project_uuid and context.project_uuid:
        from dataclasses import replace
        config = replace(config, project_uuid=context.project_uuid, project_name=context.project_name)
    return context.project_paths(), config, []


# Kept for callers that use the path-confinement helper directly.
def _resolve_relative_child(
    base_dir: Path,
    relative_path: str,
    field_name: str,
    *,
    parent_label: str,
) -> Path:
    candidate = Path(relative_path)
    resolved = (candidate if candidate.is_absolute() else base_dir / candidate).resolve(
        strict=False
    )
    try:
        resolved.relative_to(base_dir.resolve(strict=False))
    except ValueError as exc:
        raise ConfigError(f"{field_name} must stay inside {parent_label}.") from exc
    return resolved
