from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib
from ledgercore.layout import parse_ledger_project_manifest

from archledger.cli_options import InitOptions
from archledger.config.render import build_default_project_config, render_project_config
from archledger.errors import ArchledgerError
from archledger.project_context import load_project_context
from archledger.project_manifest import (
    ensure_archledger_registration,
    ensure_project_identity,
    load_manifest,
    manifest_text,
    new_manifest,
    write_manifest,
)
from archledger.repository import ArchitectureRepository, InitResult
from archledger.storage.common import ensure_dir, write_text_atomic
from archledger.storage.paths import ProjectPaths


def initialize_project(root: Path, options: InitOptions) -> InitResult:
    root = root.resolve()
    manifest_path = root / ".ledger/ledger.toml"
    config_path = root / ".ledger/arch/config.toml"

    if manifest_path.exists():
        manifest = load_manifest(manifest_path)
        raw = tomllib.loads(manifest_text(manifest))
        if (
            "ledgers" in raw
            and isinstance(raw["ledgers"], dict)
            and "archledger" in raw["ledgers"]
        ):
            parse_ledger_project_manifest(raw)
    else:
        manifest = new_manifest(
            project_uuid=options.project_uuid or str(uuid4()),
            project_name=options.project_name or root.name,
        )
    uuid, name = ensure_project_identity(
        manifest,
        project_uuid=options.project_uuid,
        project_name=options.project_name,
        default_name=root.name,
    )
    ensure_archledger_registration(manifest)
    config = build_default_project_config(
        root,
        archledger_dir="arch/archledger",
        source_format=options.source_format,
        id_prefix=options.id_prefix,
        id_width=options.id_width,
        id_segment_mode=options.id_segment_mode,
        profile=options.profile,
        project_name=name,
        project_uuid=uuid,
        build_default_format=options.build.default_format,
        build_default_output=options.build.default_output,
        build_default_output_dir=options.build.default_output_dir,
        build_include_draft=options.build.include_draft,
        build_include_superseded=options.build.include_superseded,
        build_strict=options.build.strict,
        build_keep_intermediate=options.build.keep_intermediate,
        build_converter=options.build.converter,
        build_pdf_engine=options.build.pdf_engine,
        build_reference_docx=options.build.reference_docx,
        diagram_enabled=options.diagrams.enabled,
        diagram_renderer=options.diagrams.renderer,
        diagram_default_type=options.diagrams.default_type,
        diagram_output_dir=options.diagrams.output_dir,
        diagram_image_format=options.diagrams.image_format,
        diagram_kroki_url=options.diagrams.kroki_url,
        arc42_title=options.arc42.title,
        arc42_language=options.arc42.language,
        arc42_template_version=options.arc42.template_version,
        arc42_include_help=options.arc42.include_help,
        tracking_enabled=options.tracking.enabled,
        tracking_scanner=options.tracking.scanner,
        tracking_state_file=options.tracking.state_file,
        tracking_max_file_bytes=options.tracking.max_file_bytes,
        tracking_include=options.tracking.include or None,
        tracking_exclude=options.tracking.exclude or None,
    )
    if config_path.exists() and manifest_path.exists():
        context = load_project_context(root)
        return ArchitectureRepository(
            context.project_paths(), context.config or config
        ).init()

    staging_root = root / ".ledger/arch" / f".archledger-init-{uuid4().hex}"
    staging_data = staging_root / "archledger"
    ensure_dir(staging_root)
    paths = ProjectPaths(
        workspace_root=root,
        config_root=root / ".ledger",
        manifest_path=manifest_path,
        local_config_path=root / ".ledger/ledger.local.toml",
        config_path=config_path,
        archledger_dir=staging_data,
        sections_dir=staging_data / "profiles/arc42/sections",
        records_dir=staging_data / "records",
        archive_dir=staging_data / "archive",
        build_dir=staging_root / "build",
        storage_meta_path=staging_data / "storage.yaml",
        source_state_path=staging_data / options.tracking.state_file,
        document_state_path=staging_data / "document-state.json",
    )
    result = ArchitectureRepository(paths, config).init()
    target_data = root / ".ledger/arch/archledger"
    if target_data.exists():
        if any(target_data.iterdir()):
            raise ArchledgerError(
                f"Canonical data target is not empty: {target_data}",
                details={"code": "ARCHLEDGER_DATA_ROOT_CONFLICT"},
            )
        target_data.rmdir()
    target_data.parent.mkdir(parents=True, exist_ok=True)
    staging_data.rename(target_data)
    write_text_atomic(config_path, render_project_config(config))
    write_manifest(manifest_path, manifest)
    load_project_context(root)
    created = tuple(
        target_data / path.relative_to(staging_data)
        for path in result.created_paths
        if path != staging_data and path.is_relative_to(staging_data)
    ) + (config_path, manifest_path)
    return replace(
        result,
        config_path=config_path,
        archledger_dir=target_data,
        created_paths=created,
    )
