"""Archledger schema-3 project initialization.

Creates or updates: .ledger/ledger.toml, .ledger/archledger/config.toml,
bindings, storage.yaml, and profile sections.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from archledger.cli_options import InitOptions
from archledger.config.render import build_default_project_config, render_project_config
from archledger.errors import ArchledgerError
from archledger.ledgercore_backend import (
    ensure_archledger_registration,
    initialize_archledger_bindings,
)
from archledger.project_context import load_project_context
from archledger.repository import ArchitectureRepository, InitResult
from archledger.storage.common import ensure_dir, write_text_atomic
from archledger.storage.paths import ProjectPaths


def initialize_project(root: Path, options: InitOptions) -> InitResult:
    root = root.resolve()
    manifest_path = root / ".ledger/ledger.toml"
    tool_config_path = root / ".ledger/archledger/config.toml"

    # Resolve project identity.
    project_uuid = options.project_uuid
    project_name = options.project_name or root.name

    # Ensure schema-3 manifest registration through Ledgercore.
    # When the manifest already exists, ensure_archledger_registration preserves
    # the existing UUID. Read back to capture the effective identity.
    data_storage = options.data_storage or "project"
    external_root = options.external_root
    ensure_archledger_registration(
        manifest_path,
        project_uuid=project_uuid or str(uuid4()),
        project_name=project_name,
        data_storage=data_storage,  # type: ignore[arg-type]
        external_root=external_root,
    )

    # Re-read the manifest to get the effective UUID (existing or newly generated).
    from ledgercore import read_ledger_manifest

    effective_manifest = read_ledger_manifest(manifest_path)
    project_uuid = getattr(effective_manifest, "project_uuid", project_uuid) or str(
        uuid4()
    )
    project_name = getattr(effective_manifest, "project_name", None) or project_name

    # Build Archledger tool config.
    config = build_default_project_config(
        root,
        archledger_dir="data",  # relative to data mount
        source_format=options.source_format,
        id_prefix=options.id_prefix,
        id_width=options.id_width,
        id_segment_mode=options.id_segment_mode,
        profile=options.profile,
        project_name=project_name,
        project_uuid=project_uuid,
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

    # If already initialized (config exists and context loads), run init idempotently.
    if tool_config_path.exists() and manifest_path.exists():
        try:
            context = load_project_context(root)
        except Exception:
            pass
        else:
            return ArchitectureRepository(
                context.project_paths(), context.config or config
            ).init()

    # Stage data under .ledger/archledger/.
    data_root = root / ".ledger/archledger/data"
    staging_root = root / ".ledger/archledger" / f".archledger-init-{uuid4().hex}"
    staging_data = staging_root / "data"
    ensure_dir(staging_root)
    paths = ProjectPaths(
        workspace_root=root,
        config_root=root / ".ledger",
        manifest_path=manifest_path,
        local_config_path=root / ".ledger/ledger.local.toml",
        config_path=tool_config_path,
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

    # Move staged data into target.
    if data_root.exists():
        if any(data_root.iterdir()):
            raise ArchledgerError(
                f"Canonical data target is not empty: {data_root}",
                details={"code": "ARCHLEDGER_DATA_ROOT_CONFLICT"},
            )
        data_root.rmdir()
    data_root.parent.mkdir(parents=True, exist_ok=True)
    staging_data.rename(data_root)

    # Write tool config.
    write_text_atomic(tool_config_path, render_project_config(config))

    # Initialize Ledgercore bindings.
    initialize_archledger_bindings(
        root,
        project_uuid=project_uuid,
        project_name=project_name,
        data_storage=data_storage,  # type: ignore[arg-type]
        external_root=external_root,
    )

    # Validate the result loads.
    load_project_context(root)

    created = tuple(
        data_root / path.relative_to(staging_data)
        for path in result.created_paths
        if path != staging_data and path.is_relative_to(staging_data)
    ) + (tool_config_path, manifest_path)
    return replace(
        result,
        config_path=tool_config_path,
        archledger_dir=data_root,
        created_paths=created,
    )
