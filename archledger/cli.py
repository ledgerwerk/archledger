from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, TypedDict, cast

import typer
import yaml

from archledger import __version__
from archledger.cli_formatting import (
    format_archive_message as _format_archive_message,
)
from archledger.cli_formatting import (
    format_build_message as _format_build_message,
)
from archledger.cli_formatting import (
    format_changed_message as _format_changed_message,
)
from archledger.cli_formatting import (
    format_check_message as _format_check_message,
)
from archledger.cli_formatting import (
    format_convert_sources_message as _format_convert_sources_message,
)
from archledger.cli_formatting import (
    format_doctor_message as _format_doctor_message,
)
from archledger.cli_formatting import (
    format_init_message as _format_init_message,
)
from archledger.cli_formatting import (
    format_list_message as _format_list_message,
)
from archledger.cli_formatting import (
    format_new_message as _format_new_message,
)
from archledger.cli_formatting import (
    format_profile_list_message as _format_profile_list_message,
)
from archledger.cli_formatting import (
    format_profile_migration_message as _format_profile_migration_message,
)
from archledger.cli_formatting import (
    format_read_message as _format_read_message,
)
from archledger.cli_formatting import (
    format_renumber_message as _format_renumber_message,
)
from archledger.cli_formatting import (
    format_schema_message as _format_schema_message,
)
from archledger.cli_formatting import (
    format_seed_message as _format_seed_message,
)
from archledger.cli_formatting import (
    format_show_message as _format_show_message,
)
from archledger.cli_formatting import (
    format_snapshot_message as _format_snapshot_message,
)
from archledger.cli_formatting import (
    format_status_message as _format_status_message,
)
from archledger.cli_inventory import commands_payload as _commands_payload
from archledger.cli_inventory import resolve_command as _resolve_command
from archledger.cli_payloads import (
    archive_payload as _archive_payload,
)
from archledger.cli_payloads import (
    build_result_payload as _build_payload,
)
from archledger.cli_payloads import (
    changed_payload as _changed_payload,
)
from archledger.cli_payloads import (
    check_payload as _check_payload,
)
from archledger.cli_payloads import (
    convert_sources_payload as _convert_sources_payload,
)
from archledger.cli_payloads import (
    doctor_payload as _doctor_payload,
)
from archledger.cli_payloads import (
    finding_payload as _finding_payload,
)
from archledger.cli_payloads import (
    init_result_payload as _init_payload,
)
from archledger.cli_payloads import (
    list_records_payload as _list_payload,
)
from archledger.cli_payloads import (
    new_record_payload as _new_payload,
)
from archledger.cli_payloads import (
    profile_migration_payload as _profile_migration_payload,
)
from archledger.cli_payloads import (
    read_payload as _read_payload,
)
from archledger.cli_payloads import (
    renumber_payload as _renumber_payload,
)
from archledger.cli_payloads import (
    schema_payload as _schema_payload,
)
from archledger.cli_payloads import (
    seed_payload as _seed_payload,
)
from archledger.cli_payloads import (
    show_record_payload as _show_payload,
)
from archledger.cli_payloads import (
    snapshot_payload as _snapshot_payload,
)
from archledger.cli_payloads import (
    status_payload as _status_payload,
)
from archledger.cli_runtime import (
    CommonCLIState,
    ExitCode,
)
from archledger.cli_runtime import (
    emit_error as _emit_error,
)
from archledger.cli_runtime import (
    emit_success as _emit_success,
)
from archledger.errors import ArchledgerError, StorageError
from archledger.id_format_drift import find_id_format_drift
from archledger.identity_migration import migrate_identity
from archledger.ids import DEFAULT_ID_PREFIX, DEFAULT_ID_SEGMENT_MODE, DEFAULT_ID_WIDTH
from archledger.metadata_migration import (
    metadata_migration_payload,
    migrate_metadata,
)
from archledger.migration import convert_sources
from archledger.model import ArchitectureRecord, known_source_extensions
from archledger.project_init import initialize_project
from archledger.project_migration import (
    apply_project_migration,
    inspect_project_migration,
    inspection_payload,
    migration_result_payload,
)
from archledger.render import build_document
from archledger.renumber import renumber_project
from archledger.repository import (
    ArchitectureRepository,
    CheckResult,
)
from archledger.source_tracking import (
    SourceState,
    diff_source_states,
    resolve_impacts,
    scan_workspace,
)
from archledger.storage.common import write_text_atomic
from archledger.storage.paths import (
    ProjectPaths,
    resolve_project_paths,
)
from archledger.storage.project_config import (
    ProjectConfig,
)
from archledger.storage.source_state import read_source_state, write_source_state

app = typer.Typer(add_completion=False, no_args_is_help=True)
source_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(
    source_app,
    name="source",
    help="Inspect implementation drift and convert source dialects.",
)
migrate_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(
    migrate_app,
    name="migrate",
    help="Run one-off repository migrations.",
)
profile_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(
    profile_app,
    name="profile",
    help="Manage archledger profiles (arc42).",
)
record_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(record_app, name="record", help="Safely mutate records.")
record_meta_app = typer.Typer(add_completion=False, no_args_is_help=True)
record_app.add_typer(record_meta_app, name="meta", help="Mutate record metadata.")
record_body_app = typer.Typer(add_completion=False, no_args_is_help=True)
record_app.add_typer(record_body_app, name="body", help="Mutate record bodies.")
refs_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(refs_app, name="refs", help="Manage source references.")
links_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(links_app, name="links", help="Manage record links.")
ref_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(ref_app, name="ref", help="Manage source references.")
link_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(link_app, name="link", help="Manage record links.")
ac_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(ac_app, name="ac", help="Manage inline acceptance criteria.")
scope_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(scope_app, name="scope", help="Inspect record scope metadata.")

storage_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(
    storage_app,
    name="storage",
    help="Inspect and manage Archledger storage topology.",
)


@dataclass(frozen=True, slots=True)
class VisibilityOptions:
    include_drafts: bool
    include_superseded: bool


def _resolve_visibility(
    *,
    include_drafts: bool,
    include_superseded: bool,
    all_statuses: bool,
) -> VisibilityOptions:
    return VisibilityOptions(
        include_drafts=include_drafts or all_statuses,
        include_superseded=include_superseded or all_statuses,
    )


def _version_callback(value: bool | None) -> None:
    if not value:
        return
    typer.echo(f"archledger {__version__}")
    raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    root: Annotated[
        Path | None,
        typer.Option(
            "--root",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            help="Resolve config discovery from this workspace path.",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Emit machine-readable JSON output.",
        ),
    ] = False,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the installed archledger version and exit.",
        ),
    ] = None,
) -> None:
    del version
    ctx.obj = CommonCLIState(
        tool="archledger",
        root=(Path.cwd() if root is None else root).resolve(strict=False),
        json_output=json_output,
    )


@app.command()
def init(
    ctx: typer.Context,
    archledger_dir: Annotated[
        str | None,
        typer.Option(
            "--archledger-dir",
            help="Deprecated: canonical storage is fixed below .ledger/arch.",
        ),
    ] = None,
    project_name: Annotated[
        str | None,
        typer.Option(
            "--project-name",
            help="Stable project identity stored in .ledger/ledger.toml.",
        ),
    ] = None,
    project_uuid: Annotated[
        str | None,
        typer.Option(
            "--project-uuid",
            help="Stable project UUID. Auto-generated when omitted.",
        ),
    ] = None,
    source_format: Annotated[
        str,
        typer.Option(
            "--source-format",
            help="Canonical source dialect for new project fragments.",
        ),
    ] = "markdown",
    id_prefix: Annotated[
        str,
        typer.Option("--id-prefix", help="Ledger ID prefix, e.g. al or ta."),
    ] = DEFAULT_ID_PREFIX,
    id_width: Annotated[
        int,
        typer.Option("--id-width", help="Minimum ledger ID digit width."),
    ] = DEFAULT_ID_WIDTH,
    id_segment_mode: Annotated[
        str,
        typer.Option(
            "--id-segment-mode",
            help="Ledger ID segment mode (none or type).",
        ),
    ] = DEFAULT_ID_SEGMENT_MODE,
    # Build options
    build_default_format: Annotated[
        str | None,
        typer.Option(
            "--build-default-format",
            help="Default build output format (markdown, asciidoc, pdf, docx).",
        ),
    ] = None,
    build_default_output: Annotated[
        str | None,
        typer.Option("--build-default-output", help="Default build output filename."),
    ] = None,
    build_default_output_dir: Annotated[
        str | None,
        typer.Option(
            "--build-default-output-dir",
            help="Build output directory, relative to config path.",
        ),
    ] = None,
    build_include_draft: Annotated[
        bool,
        typer.Option(
            "--build-include-draft", help="Include draft records in build output."
        ),
    ] = False,
    build_include_superseded: Annotated[
        bool,
        typer.Option(
            "--build-include-superseded",
            help="Include superseded records in build output.",
        ),
    ] = False,
    build_strict: Annotated[
        bool,
        typer.Option("--build-strict", help="Enable strict build mode."),
    ] = False,
    build_keep_intermediate: Annotated[
        bool,
        typer.Option(
            "--build-keep-intermediate", help="Keep intermediate build files."
        ),
    ] = False,
    build_converter: Annotated[
        str,
        typer.Option(
            "--build-converter",
            help="Build converter tool (auto, pandoc, asciidoctor).",
        ),
    ] = "auto",
    build_pdf_engine: Annotated[
        str,
        typer.Option("--build-pdf-engine", help="PDF engine for pandoc builds."),
    ] = "",
    build_reference_docx: Annotated[
        str,
        typer.Option(
            "--build-reference-docx", help="Reference docx template for pandoc builds."
        ),
    ] = "",
    # Diagram options
    diagrams: Annotated[
        bool,
        typer.Option("--diagrams/--no-diagrams", help="Enable diagram support."),
    ] = False,
    diagram_renderer: Annotated[
        str,
        typer.Option(
            "--diagram-renderer",
            help="Diagram renderer (pass-through, mermaid-cli, asciidoctor-diagram).",
        ),
    ] = "pass-through",
    diagram_default_type: Annotated[
        str,
        typer.Option(
            "--diagram-default-type",
            help="Default diagram type (text, ascii, unicode, svgbob, mermaid).",
        ),
    ] = "text",
    diagram_output_dir: Annotated[
        str,
        typer.Option("--diagram-output-dir", help="Diagram output directory."),
    ] = "diagrams",
    diagram_image_format: Annotated[
        str,
        typer.Option("--diagram-image-format", help="Diagram image format (svg, png)."),
    ] = "svg",
    diagram_kroki_url: Annotated[
        str,
        typer.Option(
            "--diagram-kroki-url",
            help="Kroki server URL (unused in supported renderers).",
        ),
    ] = "",
    # arc42 options
    arc42_title: Annotated[
        str,
        typer.Option("--arc42-title", help="arc42 template title."),
    ] = "Architecture Documentation",
    arc42_language: Annotated[
        str,
        typer.Option("--arc42-language", help="arc42 template language."),
    ] = "en",
    arc42_template_version: Annotated[
        str,
        typer.Option("--arc42-template-version", help="arc42 template version."),
    ] = "9.0-EN",
    arc42_include_help: Annotated[
        bool,
        typer.Option(
            "--arc42-include-help/--no-arc42-include-help",
            help="Include arc42 help sections.",
        ),
    ] = False,
    # Tracking options
    tracking: Annotated[
        bool,
        typer.Option("--tracking/--no-tracking", help="Enable source tracking."),
    ] = True,
    tracking_scanner: Annotated[
        str,
        typer.Option(
            "--tracking-scanner", help="Tracking scanner (auto, git, filesystem)."
        ),
    ] = "auto",
    tracking_state_file: Annotated[
        str,
        typer.Option("--tracking-state-file", help="Tracking state filename."),
    ] = "source-state.json",
    tracking_max_file_bytes: Annotated[
        int,
        typer.Option(
            "--tracking-max-file-bytes", help="Maximum file size in bytes for tracking."
        ),
    ] = 1_000_000,
    tracking_include: Annotated[
        list[str] | None,
        typer.Option(
            "--tracking-include", help="Glob pattern for tracking includes. Repeatable."
        ),
    ] = None,
    tracking_exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--tracking-exclude", help="Glob pattern for tracking excludes. Repeatable."
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            help="Initial project profile (arc42).",
        ),
    ] = "arc42",
) -> None:
    from archledger.cli_options import (
        InitArc42Options,
        InitBuildOptions,
        InitDiagramOptions,
        InitOptions,
        InitTrackingOptions,
    )

    state = _state(ctx)
    workspace_root = state.root.resolve()
    if archledger_dir is not None:
        _emit_error(
            state,
            "init",
            ArchledgerError(
                "--archledger-dir is no longer supported; use .ledger/arch/archledger."
            ),
        )
    legacy = [
        workspace_root / "archledger.toml",
        workspace_root / ".archledger.toml",
        workspace_root / ".archledger",
    ]
    if any(path.exists() for path in legacy):
        _emit_error(
            state,
            "init",
            ArchledgerError(
                "Legacy Archledger layout found. Run: archledger migrate project",
                details={"code": "ARCHLEDGER_MIGRATION_REQUIRED"},
            ),
        )
    try:
        opts = InitOptions(
            archledger_dir=archledger_dir or "arch/archledger",
            project_name=project_name,
            project_uuid=project_uuid,
            source_format=source_format,
            id_prefix=id_prefix,
            id_width=id_width,
            id_segment_mode=id_segment_mode,
            profile=profile,
            build=InitBuildOptions(
                default_format=build_default_format,
                default_output=build_default_output,
                default_output_dir=build_default_output_dir,
                include_draft=build_include_draft,
                include_superseded=build_include_superseded,
                strict=build_strict,
                keep_intermediate=build_keep_intermediate,
                converter=build_converter,
                pdf_engine=build_pdf_engine,
                reference_docx=build_reference_docx,
            ),
            diagrams=InitDiagramOptions(
                enabled=diagrams,
                renderer=diagram_renderer,
                default_type=diagram_default_type,
                output_dir=diagram_output_dir,
                image_format=diagram_image_format,
                kroki_url=diagram_kroki_url,
            ),
            arc42=InitArc42Options(
                title=arc42_title,
                language=arc42_language,
                template_version=arc42_template_version,
                include_help=arc42_include_help,
            ),
            tracking=InitTrackingOptions(
                enabled=tracking,
                scanner=tracking_scanner,
                state_file=tracking_state_file,
                max_file_bytes=tracking_max_file_bytes,
                include=tuple(tracking_include) if tracking_include else (),
                exclude=tuple(tracking_exclude) if tracking_exclude else (),
            ),
        )
        result = initialize_project(workspace_root, opts)
        payload = _init_payload(result)
        _emit_success(
            state,
            command="init",
            result=payload,
            warnings=[],
            human_message=_format_init_message(payload),
        )
    except ArchledgerError as exc:
        _emit_error(state, "init", exc)


@app.command()
def status(ctx: typer.Context) -> None:
    state = _state(ctx)
    from archledger.project_context import classify_project_state

    classification = classify_project_state(state.root)
    if classification in {"uninitialized", "legacy", "partial", "invalid"}:
        payload = _basic_workspace_state(state.root, classification)
        _emit_success(
            state,
            command="status",
            result=payload,
            warnings=[],
            human_message=(
                f"Archledger state: {classification}\n"
                f"Next: {payload['recommended_next']}"
            ),
        )
        return
    try:
        paths, config, _ = resolve_project_paths(state.root)
        repo = ArchitectureRepository(paths, config)
        payload = _status_payload(repo, paths, config)
        records = repo.list_records(include_draft=True, include_superseded=True)
        payload.update(
            {
                "state": "canonical",
                "registered": True,
                "initialized": True,
                "valid": True,
                "record_count": len(records),
                "draft_count": sum(1 for record in records if record.status == "draft"),
                "migration_state": "clean",
                "recommended_next": "archledger check",
            }
        )
        _emit_success(
            state,
            command="status",
            result=payload,
            warnings=[],
            human_message=_format_status_message(payload),
        )
    except ArchledgerError as exc:
        _emit_error(state, "status", exc)


@app.command()
def info(ctx: typer.Context) -> None:
    """Show a complete read-only Archledger inventory."""
    state = _state(ctx)
    from archledger.project_context import classify_project_state

    classification = classify_project_state(state.root)
    if classification != "canonical":
        payload = _basic_workspace_state(state.root, classification)
        _emit_success(
            state,
            command="info",
            result=payload,
            warnings=[],
            human_message=(
                f"Archledger state: {classification}\n"
                f"Next: {payload['recommended_next']}"
            ),
        )
        return

    try:
        from archledger.ledgercore_backend import (
            load_archledger_layout,
            validate_archledger_layout,
        )

        layout = load_archledger_layout(state.root, require_registration=False)
        validation = validate_archledger_layout(layout)
        paths, config, _ = resolve_project_paths(state.root)
        repo = ArchitectureRepository(paths, config)
        records = repo.list_records(include_draft=True, include_superseded=True)
        payload = {
            "state": classification,
            "project": {
                "root": str(layout.project_root),
                "uuid": layout.project_uuid,
                "name": layout.project_name,
            },
            "manifest_path": str(layout.manifest_path),
            "local_config_path": str(layout.local_config_path),
            "tool_config_path": str(layout.tool_config_path),
            "data_root": str(layout.data_root),
            "effective_mount": {
                "storage": layout.data_storage,
                "source": layout.data_source,
                "external_root": str(layout.external_root)
                if layout.external_root
                else None,
            },
            "binding": {
                "config": str(layout.config_binding_path),
                "data": str(layout.data_binding_path),
                "valid": validation.config_binding_valid
                and validation.data_binding_valid,
            },
            "config_version": config.config_version,
            "source_format": config.source_format,
            "profiles": list(config.profiles.profiles.enabled),
            "record_count": len(records),
            "draft_count": sum(1 for record in records if record.status == "draft"),
            "document_version": getattr(config, "document_state_version", None),
            "build_dir": str(paths.build_dir),
            "migration_journals": _trusted_migration_paths(state.root),
            "migration_receipts": [
                str(path) for path in sorted(paths.archledger_dir.glob("migrations/*"))
            ],
            "legacy_paths": [
                str(path)
                for path in (
                    state.root / ".archledger.toml",
                    state.root / ".archledger",
                )
                if path.exists()
            ],
        }
        _emit_success(
            state,
            command="info",
            result=payload,
            warnings=list(validation.warnings),
            human_message=(
                f"Archledger {layout.project_name or layout.project_uuid}\n"
                f"Records: {len(records)} (drafts: {payload['draft_count']})\n"
                f"Data: {layout.data_root}"
            ),
        )
    except ArchledgerError as exc:
        _emit_error(state, "info", exc)


@app.command()
def commands(ctx: typer.Context) -> None:
    """List the canonical command inventory and compatibility aliases."""
    state = _state(ctx)
    payload = _commands_payload()
    _emit_success(
        state,
        command="commands",
        result=payload,
        warnings=[],
        human_message="\n".join(
            f"{entry['path']}: {entry['summary']}"
            for entry in payload["commands"]
            if not entry["deprecated"]
        ),
    )


@app.command("help")
def help_command(
    ctx: typer.Context,
    command: Annotated[list[str] | None, typer.Argument()] = None,
) -> None:
    """Show inventory-driven help for a command path."""
    state = _state(ctx)
    requested = " ".join(command or [])
    if not requested:
        payload = _commands_payload()
        message = (
            "Use `archledger help COMMAND` for nested command help.\n\n"
            + "\n".join(
                f"{entry['path']}: {entry['summary']}"
                for entry in payload["commands"]
                if not entry["deprecated"]
            )
        )
        _emit_success(
            state, command="help", result=payload, warnings=[], human_message=message
        )
        return
    entry = _resolve_command(requested)
    if entry is None:
        _emit_error(
            state,
            "help",
            ArchledgerError(
                f"Unknown command path: {requested}",
                details={
                    "code": "invalid_arguments",
                    "remediation": ["Run: archledger commands"],
                },
            ),
        )
    payload = {"command": entry.as_mapping()}
    _emit_success(
        state,
        command="help",
        result=payload,
        warnings=[],
        human_message=f"{entry.path}\n\n{entry.summary}",
    )


@app.command("next-action")
def next_action(ctx: typer.Context) -> None:
    """Recommend the next safe read-only or lifecycle action."""
    state = _state(ctx)
    from archledger.project_context import classify_project_state

    classification = classify_project_state(state.root)
    actions = {
        "uninitialized": ("archledger init", "No Archledger project is initialized."),
        "legacy": (
            "archledger migrate plan project-layout",
            "A legacy Archledger source was detected.",
        ),
        "partial": (
            "archledger storage validate --strict",
            "The canonical project is incomplete.",
        ),
        "invalid": (
            "archledger doctor",
            "The workspace or canonical configuration is invalid.",
        ),
        "canonical": ("archledger check", "The canonical project is ready for checks."),
    }
    recommended, reason = actions[classification]
    payload = {
        "state": classification,
        "recommended_next": recommended,
        "reason": reason,
    }
    _emit_success(
        state,
        command="next-action",
        result=payload,
        warnings=[],
        human_message=f"Next action: {recommended}\n{reason}",
    )


@app.command("paths", deprecated=True)
def paths(ctx: typer.Context) -> None:
    """Deprecated: use `archledger storage where` instead."""
    state = _state(ctx)
    from archledger.project_context import classify_project_state

    if classify_project_state(state.root) != "canonical":
        payload = _basic_workspace_state(state.root, "legacy")
        _emit_success(
            state,
            command="paths",
            result=payload,
            warnings=[
                {
                    "code": "deprecated_command",
                    "message": (
                        "`archledger paths` is deprecated; use `archledger "
                        "storage where` instead."
                    ),
                    "replacement": "storage where",
                }
            ],
            human_message=f"Archledger state: {payload['state']}",
        )
        return
    try:
        payload, msg = _build_storage_where_output(state.root)
        _emit_success(
            state, command="paths", result=payload, warnings=[], human_message=msg
        )
    except ArchledgerError as exc:
        _emit_error(state, "paths", exc)


@storage_app.command("where")
def storage_where(ctx: typer.Context) -> None:
    """Show resolved project identity and storage paths."""
    state = _state(ctx)
    from archledger.project_context import classify_project_state

    if classify_project_state(state.root) != "canonical":
        classification = classify_project_state(state.root)
        payload = _basic_workspace_state(state.root, classification)
        if (
            classification == "invalid"
            and not payload["registered"]
            and (payload["tool_config_exists"] or payload["data_root_exists"])
        ):
            payload["state"] = "unregistered-with-residual-state"
        _emit_success(
            state,
            command="storage where",
            result=payload,
            warnings=[],
            human_message=(
                f"Archledger storage state: {payload['state']}\n"
                f"Next: {payload['recommended_next']}"
            ),
        )
        return
    try:
        payload, msg = _build_storage_where_output(state.root)
        _emit_success(
            state,
            command="storage where",
            result=payload,
            warnings=[],
            human_message=msg,
        )
    except ArchledgerError as exc:
        _emit_error(state, "storage where", exc)


@storage_app.command("validate")
def storage_validate(
    ctx: typer.Context,
    strict: Annotated[bool, typer.Option("--strict")] = False,
) -> None:
    """Validate Ledgercore layout/bindings and Archledger domain storage."""
    state = _state(ctx)
    try:
        from archledger.ledgercore_backend import (
            load_archledger_layout,
            validate_archledger_layout,
        )

        layout = load_archledger_layout(state.root, require_registration=False)
        validation = validate_archledger_layout(layout)
        payload = {
            "schema": "archledger.storage-validation.v1",
            "valid": validation.valid,
            "registered": layout.raw_effective is not None,
            "effective_registration_present": layout.raw_effective is not None,
            "state": (
                "registered"
                if layout.raw_effective is not None
                else "unregistered-with-residual-state"
            ),
            "config_binding_valid": validation.config_binding_valid,
            "data_binding_valid": validation.data_binding_valid,
            "mounts_valid": validation.mounts_valid,
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        }
        lines = [f"Storage validation: {'PASSED' if validation.valid else 'FAILED'}"]
        for err in validation.errors:
            lines.append(f"  ERROR: {err}")
        for warn in validation.warnings:
            lines.append(f"  WARN:  {warn}")
        _emit_success(
            state,
            command="storage validate",
            result=payload,
            warnings=[],
            human_message="\n".join(lines),
        )
        if strict and not validation.valid:
            raise typer.Exit(code=1)
    except ArchledgerError as exc:
        _emit_error(state, "storage validate", exc)


@storage_app.command("set")
def storage_set(
    ctx: typer.Context,
    mount: Annotated[str, typer.Argument()] = "data",
    storage: Annotated[str, typer.Option("--storage")] = "project",
    storage_root: Annotated[Path | None, typer.Option("--storage-root")] = None,
    scope: Annotated[str, typer.Option("--scope")] = "project",
    reason: Annotated[str, typer.Option("--reason")] = "",
) -> None:
    """Change storage topology without moving authoritative data."""
    state = _state(ctx)
    if mount != "data":
        _emit_error(
            state,
            "storage set",
            ArchledgerError(
                "Archledger exposes only the data mount.",
                details={"code": "invalid_arguments"},
            ),
        )
    if storage not in {"project", "external", "user-data"}:
        _emit_error(
            state,
            "storage set",
            ArchledgerError(
                "--storage must be project, external, or user-data.",
                details={"code": "invalid_arguments"},
            ),
        )
    if scope not in {"project", "local"}:
        _emit_error(
            state,
            "storage set",
            ArchledgerError(
                "--scope must be project or local.",
                details={"code": "invalid_arguments"},
            ),
        )
    if storage == "external" and storage_root is None:
        _emit_error(
            state,
            "storage set",
            ArchledgerError(
                "--storage-root is required for external storage.",
                details={"code": "invalid_arguments"},
            ),
        )
    if not reason:
        _emit_error(
            state,
            "storage set",
            ArchledgerError(
                "--reason is required for storage topology changes.",
                details={"code": "invalid_arguments"},
            ),
        )
    try:
        from archledger.ledgercore_backend import (
            ensure_archledger_registration,
            load_archledger_layout,
            set_archledger_data_override,
        )

        layout = load_archledger_layout(state.root, require_registration=True)
        old_root = layout.data_root
        old_storage = layout.data_storage
        if scope == "local":
            set_archledger_data_override(
                layout.local_config_path,
                data_storage=storage,
                external_root=str(storage_root) if storage_root else None,
            )
        else:
            ensure_archledger_registration(
                layout.manifest_path,
                project_uuid=layout.project_uuid,
                project_name=layout.project_name,
                data_storage=storage,
                external_root=str(storage_root) if storage_root else None,
            )
        updated = load_archledger_layout(state.root, require_registration=True)
        data_present = old_root.is_dir() and any(old_root.iterdir())
        changed = old_root.resolve(strict=False) != updated.data_root.resolve(
            strict=False
        )
        payload = {
            "mount": mount,
            "scope": scope,
            "reason": reason,
            "old_storage": old_storage,
            "new_storage": updated.data_storage,
            "old_data_root": str(old_root),
            "new_data_root": str(updated.data_root),
            "data_moved": False,
            "authoritative_data_present": data_present,
            "topology_changed": changed,
            "recommended_next": (
                "archledger migrate plan storage-layout" if changed else None
            ),
        }
        _emit_success(
            state,
            command="storage set",
            result=payload,
            warnings=[],
            human_message=(
                f"Storage topology updated: {old_root} -> {updated.data_root}\n"
                "No data was moved."
            ),
        )
    except ArchledgerError as exc:
        _emit_error(state, "storage set", exc)


@storage_app.command("clear-override")
def storage_clear_override(
    ctx: typer.Context,
    mount: Annotated[str, typer.Argument()] = "data",
    reason: Annotated[str, typer.Option("--reason")] = "",
) -> None:
    """Clear the local data topology override without moving data."""
    state = _state(ctx)
    if mount != "data":
        _emit_error(
            state,
            "storage clear-override",
            ArchledgerError(
                "Archledger exposes only the data mount.",
                details={"code": "invalid_arguments"},
            ),
        )
    if not reason:
        _emit_error(
            state,
            "storage clear-override",
            ArchledgerError(
                "--reason is required for storage topology changes.",
                details={"code": "invalid_arguments"},
            ),
        )
    try:
        from archledger.ledgercore_backend import (
            clear_archledger_data_override,
            load_archledger_layout,
        )

        before = load_archledger_layout(state.root, require_registration=True)
        clear_archledger_data_override(before.local_config_path)
        after = load_archledger_layout(state.root, require_registration=True)
        _emit_success(
            state,
            command="storage clear-override",
            result={
                "mount": mount,
                "reason": reason,
                "old_data_root": str(before.data_root),
                "new_data_root": str(after.data_root),
                "data_moved": False,
                "recommended_next": (
                    "archledger migrate plan storage-layout"
                    if before.data_root != after.data_root
                    else None
                ),
            },
            warnings=[],
            human_message=(
                f"Storage override cleared. Effective data: {after.data_root}"
            ),
        )
    except ArchledgerError as exc:
        _emit_error(state, "storage clear-override", exc)


@app.command("schema")
def schema(
    ctx: typer.Context,
    output_format: Annotated[str, typer.Option("--format")] = "summary",
    target: Annotated[str | None, typer.Option("--target")] = None,
) -> None:
    if output_format == "summary":
        _run_simple_command(ctx, "schema", _schema_payload, _format_schema_message)
        return
    if output_format != "jsonschema" or target is None:
        raise ArchledgerError(
            "--format must be summary or jsonschema; jsonschema requires --target."
        )
    from archledger.jsonschemas import load_json_schema

    state = _state(ctx)
    try:
        payload = load_json_schema(target)
        _emit_success(
            state,
            command="schema",
            result=payload,
            warnings=[],
            human_message=json.dumps(payload, indent=2, sort_keys=True),
        )
    except ArchledgerError as exc:
        _emit_error(state, "schema", exc)


@app.command("new")
def new_record(
    ctx: typer.Context,
    kind: Annotated[str, typer.Argument()],
    title: Annotated[
        str,
        typer.Argument(help="Human-readable record title."),
    ],
    parent: Annotated[
        str | None,
        typer.Option("--parent", help="Optional parent record ID."),
    ] = None,
    status: Annotated[
        str,
        typer.Option("--status", help="Initial record status."),
    ] = "draft",
    section: Annotated[
        str | None,
        typer.Option(
            "--section",
            help="Override the default target section.",
        ),
    ] = None,
    context_kind: Annotated[
        str | None,
        typer.Option(
            "--context-kind",
            help="Context classification for context-interface records.",
        ),
    ] = None,
    partner: Annotated[
        str | None,
        typer.Option(
            "--partner",
            help="Partner or external system for context-interface records.",
        ),
    ] = None,
    environment: Annotated[
        str | None,
        typer.Option(
            "--environment",
            help="Environment for infrastructure or quality-scenario records.",
        ),
    ] = None,
    quality: Annotated[
        str | None,
        typer.Option(
            "--quality",
            help="Quality attribute for quality-scenario records.",
        ),
    ] = None,
    diagram_type: Annotated[
        str | None,
        typer.Option(
            "--diagram-type",
            help="Diagram type for diagram records (default: mermaid).",
        ),
    ] = None,
    caption: Annotated[
        str | None,
        typer.Option(
            "--caption",
            help="Diagram caption for diagram records.",
        ),
    ] = None,
    related_records: Annotated[
        list[str] | None,
        typer.Option(
            "--related",
            help="Related record ID for diagram records. Repeatable.",
        ),
    ] = None,
    requirement: Annotated[
        str | None,
        typer.Option(
            "--requirement",
            help="Requirement record ID for acceptance-criterion records.",
        ),
    ] = None,
    validation_command: Annotated[
        str | None,
        typer.Option(
            "--validation-command",
            help="Validation command for acceptance-criterion records.",
        ),
    ] = None,
    validation_expected: Annotated[
        str | None,
        typer.Option(
            "--validation-expected",
            help=(
                "Expected result for acceptance-criterion validation (default: passes)."
            ),
        ),
    ] = None,
) -> None:
    state = _state(ctx)

    def _build_new_record_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths
        return _new_payload(
            repo.create_record(
                kind,
                title,
                parent=parent,
                status=status,
                section=section,
                context_kind=context_kind,
                partner=partner,
                environment=environment,
                quality=quality,
                diagram_type=diagram_type,
                caption=caption,
                related_records=related_records or [],
                requirement=requirement,
                validation_command=validation_command,
                validation_expected=validation_expected,
            ),
            config,
        )

    canonical = ctx.parent is not None and ctx.parent.command.name == "record"
    _run_configured_command(
        state,
        "record create" if canonical else "new",
        _build_new_record_result,
        _format_new_message,
        extra_warnings=[]
        if canonical
        else [
            {
                "code": "deprecated_command",
                "message": (
                    "`archledger new` is deprecated; use `archledger record "
                    "create` instead."
                ),
                "replacement": "record create",
            }
        ],
    )


record_app.command("create")(new_record)


@app.command()
def seed(
    ctx: typer.Context,
    preset: Annotated[str, typer.Argument()],
) -> None:
    state = _state(ctx)

    def _build_seed_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths
        if preset == "arc42-minimal":
            records = _seed_arc42_minimal(repo)
        else:
            raise ArchledgerError(f"Unsupported seed preset: {preset}")
        return _seed_payload(preset, records, config)

    _run_configured_command(state, "seed", _build_seed_result, _format_seed_message)


@app.command("list")
def list_records(
    ctx: typer.Context,
    kind: Annotated[str | None, typer.Argument()] = None,
    include_drafts: Annotated[bool, typer.Option("--include-drafts")] = False,
    include_superseded: Annotated[bool, typer.Option("--include-superseded")] = False,
    all_statuses: Annotated[bool, typer.Option("--all-statuses")] = False,
    scope: Annotated[str | None, typer.Option("--scope")] = None,
) -> None:
    state = _state(ctx)
    visibility = _resolve_visibility(
        include_drafts=include_drafts,
        include_superseded=include_superseded,
        all_statuses=all_statuses,
    )

    def _build_list_records_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths
        return _list_payload(
            repo.list_records(
                include_draft=visibility.include_drafts,
                include_superseded=visibility.include_superseded,
                kind=kind,
                scope=scope,
            ),
            config,
        )

    canonical = ctx.parent is not None and ctx.parent.command.name == "record"
    _run_configured_command(
        state,
        "record list" if canonical else "list",
        _build_list_records_result,
        _format_list_message,
        extra_warnings=[]
        if canonical
        else [
            {
                "code": "deprecated_command",
                "message": (
                    "`archledger list` is deprecated; use `archledger record "
                    "list` instead."
                ),
                "replacement": "record list",
            }
        ],
    )


record_app.command("list")(list_records)


@app.command()
def show(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
) -> None:
    state = _state(ctx)

    def _build_show_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths
        return _show_payload(repo.get_record(record_id), config)

    canonical = ctx.parent is not None and ctx.parent.command.name == "record"
    _run_configured_command(
        state,
        "record show" if canonical else "show",
        _build_show_result,
        _format_show_message,
        extra_warnings=[]
        if canonical
        else [
            {
                "code": "deprecated_command",
                "message": (
                    "`archledger show` is deprecated; use `archledger record "
                    "show` instead."
                ),
                "replacement": "record show",
            }
        ],
    )


record_app.command("show")(show)


@app.command()
def read(
    ctx: typer.Context,
    body: Annotated[bool, typer.Option("--body")] = False,
    include_drafts: Annotated[bool, typer.Option("--include-drafts")] = False,
    include_superseded: Annotated[bool, typer.Option("--include-superseded")] = False,
    all_statuses: Annotated[bool, typer.Option("--all-statuses")] = False,
    section: Annotated[str | None, typer.Option("--section")] = None,
    kind: Annotated[str | None, typer.Option("--kind")] = None,
    scope: Annotated[str | None, typer.Option("--scope")] = None,
    scope_kind: Annotated[str | None, typer.Option("--scope-kind")] = None,
    addon: Annotated[str | None, typer.Option("--addon")] = None,
) -> None:
    state = _state(ctx)
    visibility = _resolve_visibility(
        include_drafts=include_drafts,
        include_superseded=include_superseded,
        all_statuses=all_statuses,
    )

    def _build_read_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        return _read_payload(
            repo,
            paths,
            config,
            include_body=body,
            include_draft=visibility.include_drafts,
            include_superseded=visibility.include_superseded,
            section=section,
            kind=kind,
            scope=scope,
            scope_kind=scope_kind,
            addon=addon,
        )

    canonical = ctx.parent is not None and ctx.parent.command.name == "record"
    _run_configured_command(
        state,
        "record read" if canonical else "read",
        _build_read_result,
        _format_read_message,
        extra_warnings=[]
        if canonical
        else [
            {
                "code": "deprecated_command",
                "message": (
                    "`archledger read` is deprecated; use `archledger record "
                    "read` instead."
                ),
                "replacement": "record read",
            }
        ],
    )


record_app.command("read")(read)


@app.command()
def check(
    ctx: typer.Context,
    strict: Annotated[bool, typer.Option("--strict")] = False,
) -> None:
    state = _state(ctx)

    def _build_check_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        result = repo.check(strict=strict)
        if result.has_failures(strict=strict):
            raise _check_error(result, strict=strict)
        return _check_payload(result)

    _run_configured_command(state, "check", _build_check_result, _format_check_message)


@app.command("archive")
def archive(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument(help="Ledger ID to archive.")],
    reason: Annotated[str, typer.Option("--reason", help="Archive reason.")] = "",
) -> None:
    state = _state(ctx)

    def _build_archive_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        return _archive_payload(repo.archive_record(record_id, reason=reason))

    canonical = ctx.parent is not None and ctx.parent.command.name == "record"
    _run_configured_command(
        state,
        "record archive" if canonical else "archive",
        _build_archive_result,
        _format_archive_message,
        extra_warnings=[]
        if canonical
        else [
            {
                "code": "deprecated_command",
                "message": (
                    "`archledger archive` is deprecated; use `archledger record "
                    "archive` instead."
                ),
                "replacement": "record archive",
            }
        ],
    )


record_app.command("archive")(archive)


@app.command("doctor")
def doctor(
    ctx: typer.Context,
    repair: Annotated[bool, typer.Option("--repair")] = False,
) -> None:
    state = _state(ctx)
    from archledger.project_context import classify_project_state

    classification = classify_project_state(state.root)
    if classification != "canonical" and not repair:
        payload = _basic_workspace_state(state.root, classification)
        payload.update(
            {
                "schema": "archledger.doctor.v1",
                "errors": [],
                "warnings": [],
                "repairs": [],
            }
        )
        _emit_success(
            state,
            command="doctor",
            result=payload,
            warnings=[],
            human_message=(
                f"Doctor state: {classification}\nNext: {payload['recommended_next']}"
            ),
        )
        return

    def _build_doctor_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths
        result = repo.doctor(repair=repair)
        if result.errors:
            raise ArchledgerError(
                f"Doctor found {len(result.errors)} error(s).",
                details=_doctor_payload(
                    result,
                    id_format=config.id_format,
                ),
            )
        return _doctor_payload(
            result,
            id_format=config.id_format,
        )

    _run_configured_command(
        state, "doctor", _build_doctor_result, _format_doctor_message
    )


@app.command("renumber")
def renumber(
    ctx: typer.Context,
    from_prefix: Annotated[
        str | None,
        typer.Option("--from-prefix", help="Old ledger ID prefix."),
    ] = None,
    from_width: Annotated[
        int | None,
        typer.Option("--from-width", help="Old ledger ID digit width."),
    ] = None,
    from_id_segment_mode: Annotated[
        str | None,
        typer.Option(
            "--from-id-segment-mode", help="Old ID segment mode: none or type."
        ),
    ] = None,
    prefix: Annotated[
        str | None,
        typer.Option("--prefix", help="New ledger ID prefix."),
    ] = None,
    width: Annotated[
        int | None,
        typer.Option("--width", help="New ledger ID digit width."),
    ] = None,
    id_segment_mode: Annotated[
        str | None,
        typer.Option("--id-segment-mode", help="New ID segment mode: none or type."),
    ] = None,
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Apply the renumbering plan."),
    ] = False,
    prune_generated_tombstones: Annotated[
        bool,
        typer.Option(
            "--prune-generated-tombstones",
            help="Quarantine generated tombstones that collide with living records.",
        ),
    ] = False,
) -> None:
    state = _state(ctx)

    def _build_renumber_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        explicit_from = (
            from_prefix is not None
            or from_width is not None
            or from_id_segment_mode is not None
        )
        effective_from_prefix = from_prefix
        effective_from_width = from_width
        effective_from_segment_mode = from_id_segment_mode
        if not explicit_from:
            drift = find_id_format_drift(
                paths,
                config,
                known_source_extensions(config),
            )
            if drift:
                detected_formats = {
                    (
                        item.detected_format.prefix,
                        item.detected_format.width,
                        item.detected_format.segment_mode,
                    )
                    for item in drift
                }
                if len(detected_formats) != 1:
                    raise ArchledgerError(
                        "Cannot infer previous ledger ID format from mixed source "
                        "files. Re-run renumber with explicit --from-* options."
                    )
                detected_prefix, detected_width, detected_segment_mode = next(
                    iter(detected_formats)
                )
                effective_from_prefix = detected_prefix
                effective_from_width = detected_width
                effective_from_segment_mode = detected_segment_mode
            else:
                doctor_result = repo.doctor(repair=False)
                if doctor_result.errors:
                    raise ArchledgerError(
                        (
                            "Ledger numbering is inconsistent."
                            " Run archledger doctor --repair first."
                        ),
                        details=_doctor_payload(
                            doctor_result,
                            id_format=config.id_format,
                        ),
                    )
        result = renumber_project(
            paths,
            config,
            old_prefix=effective_from_prefix,
            old_width=effective_from_width,
            old_segment_mode=effective_from_segment_mode,
            new_prefix=prefix,
            new_width=width,
            new_segment_mode=id_segment_mode,
            apply=apply,
            prune_generated_tombstones=prune_generated_tombstones,
        )
        return _renumber_payload(result)

    _run_configured_command(
        state,
        "renumber",
        _build_renumber_result,
        _format_renumber_message,
    )


@migrate_app.command("ids")
def migrate_ids(
    ctx: typer.Context,
    to: Annotated[str, typer.Option("--to")] = "ledgercore",
    apply: Annotated[bool, typer.Option("--apply")] = False,
) -> None:
    state = _state(ctx)
    if to != "ledgercore":
        raise ArchledgerError("--to must be ledgercore.")

    def _build_migrate_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo
        result = migrate_identity(paths, config, apply=apply)
        return {
            "schema": "archledger.migrate-ids.v1",
            "apply": result.apply,
            "ledger_code": result.ledger_code,
            "migrated_count": len(result.migrated),
            "rewritten_count": len(result.rewritten),
            "migrated": [
                {
                    "old_id": item.old_id,
                    "new_id": item.new_id,
                    "old_ref": item.old_ref,
                    "new_ref": item.new_ref,
                    "from": str(item.old_path),
                    "to": str(item.new_path),
                }
                for item in result.migrated
            ],
            "rewritten": [
                {"path": str(item.path), "replacement_count": item.replacement_count}
                for item in result.rewritten
            ],
            "config_path": str(result.config_path),
            "storage_next_number_before": result.storage_next_number_before,
            "storage_next_number_after": result.storage_next_number_after,
        }

    def _fmt(payload: dict[str, object]) -> str:
        return (
            f"Identity migration planned: {payload.get('migrated_count', 0)} file(s) "
            f"({payload.get('rewritten_count', 0)} rewritten)."
            if not apply
            else (
                f"Identity migration applied: "
                f"{payload.get('migrated_count', 0)} file(s) "
                f"({payload.get('rewritten_count', 0)} rewritten)."
            )
        )

    deprecation_warnings = [
        "'migrate ids --to ledgercore' is deprecated."
        " Use 'migrate plan identity-ledgercore' instead."
    ]
    if apply:
        deprecation_warnings.append(
            "'migrate ids --to ledgercore --apply' is deprecated."
            " Use 'migrate apply identity-ledgercore' instead."
        )
    _run_configured_command(
        state,
        "migrate ids",
        _build_migrate_result,
        _fmt,
        extra_warnings=deprecation_warnings,
    )


@migrate_app.command("metadata")
def migrate_metadata_command(
    ctx: typer.Context,
    to: Annotated[str, typer.Option("--to")] = "versioned",
    apply: Annotated[bool, typer.Option("--apply")] = False,
) -> None:
    state = _state(ctx)
    if to.strip().lower() != "versioned":
        raise typer.BadParameter("--to must be versioned.")

    def _build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo
        return metadata_migration_payload(migrate_metadata(paths, config, apply=apply))

    def _format(payload: dict[str, object]) -> str:
        action = "Applied" if payload["apply"] else "Planned"
        return (
            f"{action} metadata migration: "
            f"{payload['records_changed']} source file(s), "
            f"storage_changed={payload['storage_changed']}, "
            f"source_state_changed={payload['source_state_changed']}, "
            f"config_changed={payload['config_changed']}."
        )

    deprecation_warnings = [
        "'migrate metadata --to versioned' is deprecated."
        " Use 'migrate plan metadata-versioned' instead."
    ]
    if apply:
        deprecation_warnings.append(
            "'migrate metadata --to versioned --apply' is deprecated."
            " Use 'migrate apply metadata-versioned' instead."
        )
    _run_configured_command(
        state,
        "migrate metadata",
        _build_result,
        _format,
        extra_warnings=deprecation_warnings,
    )


@migrate_app.command("project")
def migrate_project(
    ctx: typer.Context,
    apply: Annotated[bool, typer.Option("--apply")] = False,
    source_config: Annotated[Path | None, typer.Option("--source-config")] = None,
    backup_dir: Annotated[Path | None, typer.Option("--backup-dir")] = None,
    retire_source: Annotated[bool, typer.Option("--retire-source")] = False,
) -> None:
    state = _state(ctx)
    try:
        # Add deprecation warning
        warnings = [
            "'migrate project' is deprecated."
            " Use 'migrate plan project-layout' instead."
        ]
        if apply:
            warnings.append(
                "'migrate project --apply' is deprecated."
                " Use 'migrate apply project-layout' instead."
            )
        inspection = inspect_project_migration(state.root, source_config=source_config)
        payload = (
            migration_result_payload(
                apply_project_migration(
                    inspection, backup_dir=backup_dir, retire_source=retire_source
                )
            )
            if apply
            else inspection_payload(inspection)
        )
        _emit_success(
            state,
            command="migrate project",
            result=payload,
            warnings=warnings,
            human_message="Project migration ready."
            if not apply
            else "Project migration applied.",
        )
    except ArchledgerError as exc:
        _emit_error(state, "migrate project", exc)


@migrate_app.command("status")
def migrate_status(
    ctx: typer.Context,
) -> None:
    """Report migration state and available migrations."""
    state = _state(ctx)
    try:
        from archledger.migrations.status import evaluate_migration_status

        report = evaluate_migration_status(state.root)
        _emit_success(
            state,
            command="migrate status",
            result=report.to_dict(),
            warnings=list(report.warnings),
            human_message=f"Migration state: {report.state.value}\n"
            + (
                f"Available: {', '.join(report.available_migrations)}\n"
                if report.available_migrations
                else ""
            )
            + (
                f"Completed: {', '.join(report.completed_migrations)}\n"
                if report.completed_migrations
                else ""
            )
            + (
                f"Pending: {', '.join(report.pending_migrations)}\n"
                if report.pending_migrations
                else ""
            )
            + (f"Next: {report.recommended_next}\n" if report.recommended_next else ""),
        )
    except ArchledgerError as exc:
        _emit_error(state, "migrate status", exc)


@migrate_app.command("plan")
def migrate_plan(
    ctx: typer.Context,
    migration: Annotated[str, typer.Argument(help="Migration name")],
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    identity_policy: Annotated[str, typer.Option("--identity-policy")] = "strict",
    storage: Annotated[str, typer.Option("--storage")] = "project",
    external_root: Annotated[Path | None, typer.Option("--external-root")] = None,
) -> None:
    """Create a deterministic migration plan."""
    state = _state(ctx)
    try:
        from archledger.migrations.plan_io import save_plan
        from archledger.migrations.registry import get_handler

        handler = get_handler(migration)
        if handler is None:
            raise StorageError(f"Unknown migration: {migration}")
        plan = handler.plan(
            state.root,
            {
                "identity_policy": identity_policy,
                "storage": storage,
                "external_root": str(external_root) if external_root else None,
            },
        )
        if output:
            save_plan(plan, output)
        _emit_success(
            state,
            command=f"migrate plan {migration}",
            result=plan.to_dict(),
            warnings=list(plan.warnings),
            human_message=f"Migration plan created for {migration}"
            + (f"\nSaved to {output}" if output else ""),
        )
    except ArchledgerError as exc:
        _emit_error(state, f"migrate plan {migration}", exc)


@migrate_app.command("apply")
def migrate_apply(
    ctx: typer.Context,
    migration: Annotated[str, typer.Argument(help="Migration name")],
    plan_file: Annotated[Path | None, typer.Option("--plan-file")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    reason: Annotated[str, typer.Option("--reason")] = "",
) -> None:
    """Execute a migration plan with journaling."""
    state = _state(ctx)
    try:
        from archledger.migrations.plan_io import load_plan
        from archledger.migrations.registry import get_handler

        handler = get_handler(migration)
        if handler is None:
            raise StorageError(f"Unknown migration: {migration}")
        if not reason and not dry_run:
            raise StorageError("--reason is required for apply")
        if plan_file:
            try:
                plan = load_plan(plan_file)
            except ValueError as exc:
                raise StorageError(
                    str(exc),
                    details={
                        "code": "stale_plan",
                        "remediation": [
                            "Recreate the plan with: "
                            "archledger migrate plan {migration}"
                        ],
                    },
                ) from exc
        else:
            plan = handler.plan(state.root, {})
        if plan.migration != migration:
            raise StorageError(
                (
                    f"Plan migration {plan.migration!r} does not match requested "
                    f"migration {migration!r}."
                ),
                details={"code": "stale_plan"},
            )
        result = handler.apply(
            state.root, plan, dry_run=dry_run, reason=reason or "dry-run"
        )
        _emit_success(
            state,
            command=f"migrate apply {migration}",
            result=result,
            warnings=[],
            human_message=f"Migration {migration} applied"
            if not dry_run
            else f"Dry run completed for {migration}",
        )
    except ArchledgerError as exc:
        # Use exit code 4 for stale/conflicting plans
        exit_code = (
            ExitCode.CONFLICT
            if exc.details.get("code") == "stale_plan"
            else ExitCode.DOMAIN_FAILURE
        )
        _emit_error(state, f"migrate apply {migration}", exc, exit_code=exit_code)


@migrate_app.command("recover")
def migrate_recover(
    ctx: typer.Context,
    journal: Annotated[Path, typer.Option("--journal")],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Recover from an interrupted migration."""
    state = _state(ctx)
    try:
        from archledger.ledgercore_backend import (
            inspect_storage_migration,
            load_archledger_layout,
        )
        from archledger.migrations.registry import get_handler

        resolved_journal = journal.resolve(strict=False)
        allowed_roots = {
            (state.root / ".ledger" / "migrations").resolve(strict=False),
            (state.root / ".ledger" / "archledger" / "migrations").resolve(
                strict=False
            ),
        }
        if (
            resolved_journal.is_symlink()
            or not resolved_journal.is_file()
            or not any(resolved_journal.parent == allowed for allowed in allowed_roots)
        ):
            raise StorageError(
                "Journal must be a regular file in the project's migrations directory.",
                details={"code": "invalid_journal_path"},
            )
        inspected = inspect_storage_migration(resolved_journal)
        migration_name = "storage-layout"
        try:
            import tomllib

            journal_data = tomllib.loads(resolved_journal.read_text(encoding="utf-8"))
            if isinstance(journal_data.get("migration"), str):
                migration_name = journal_data["migration"]
        except Exception:
            pass
        handler = get_handler(migration_name)
        if handler is None:
            raise StorageError(f"Unknown migration: {migration_name}")
        try:
            layout = load_archledger_layout(state.root, require_registration=True)
            if inspected.project_uuid != layout.project_uuid:
                raise StorageError(
                    "Journal project identity does not match the current project.",
                    details={"code": "project_uuid_mismatch"},
                )
        except ArchledgerError:
            raise
        result = handler.recover(state.root, resolved_journal, dry_run=dry_run)
        _emit_success(
            state,
            command="migrate recover",
            result=result,
            warnings=[],
            human_message="Recovery completed"
            if not dry_run
            else "Recovery dry run completed",
        )
    except ArchledgerError as exc:
        _emit_error(state, "migrate recover", exc)


@migrate_app.command("cleanup")
def migrate_cleanup(
    ctx: typer.Context,
    migration: Annotated[str, typer.Argument(help="Migration name")],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y")] = False,
    reason: Annotated[str, typer.Option("--reason")] = "",
) -> None:
    """Remove verified legacy source after migration."""
    state = _state(ctx)
    try:
        from archledger.migrations.registry import get_handler

        handler = get_handler(migration)
        if handler is None:
            raise StorageError(f"Unknown migration: {migration}")
        if not dry_run:
            if not yes:
                raise StorageError("--yes is required for cleanup")
            if not reason:
                raise StorageError("--reason is required for cleanup")
        result = handler.cleanup(
            state.root, dry_run=dry_run, yes=yes, reason=reason or "dry-run"
        )
        _emit_success(
            state,
            command=f"migrate cleanup {migration}",
            result=result,
            warnings=[],
            human_message=f"Cleanup completed for {migration}"
            if not dry_run
            else f"Cleanup dry run for {migration}",
        )
    except ArchledgerError as exc:
        _emit_error(state, f"migrate cleanup {migration}", exc)


@source_app.command("snapshot")
def snapshot(
    ctx: typer.Context,
    reason: Annotated[str, typer.Option("--reason")] = "manual",
) -> None:
    state = _state(ctx)

    def _build_snapshot_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        repo.status()
        if not config.tracking_enabled:
            raise StorageError(
                "Source tracking is disabled by [tracking].enabled = false."
            )
        existing_state = _load_tracking_baseline(paths, config)
        next_version = 1 if existing_state is None else existing_state.version + 1
        scanned_state = scan_workspace(
            paths,
            config,
            reason=reason,
            version=next_version,
        )
        write_source_state(paths.source_state_path, scanned_state)
        return _snapshot_payload(paths, scanned_state)

    _run_configured_command(
        state,
        "source snapshot",
        _build_snapshot_result,
        _format_snapshot_message,
    )


@source_app.command("changed")
def changed(
    ctx: typer.Context,
    include_drafts: Annotated[bool, typer.Option("--include-drafts")] = False,
    include_superseded: Annotated[bool, typer.Option("--include-superseded")] = False,
    all_statuses: Annotated[bool, typer.Option("--all-statuses")] = False,
    against: Annotated[
        str | None,
        typer.Option(
            "--against",
            help="Compare against a git revision (e.g. origin/main).",
        ),
    ] = None,
    since_merge_base: Annotated[
        str | None,
        typer.Option(
            "--since-merge-base",
            help="Compare against merge-base with revision (e.g. origin/main).",
        ),
    ] = None,
    fail_on_unlinked: Annotated[
        bool,
        typer.Option(
            "--fail-on-unlinked",
            help="Exit non-zero when unlinked changed files exist.",
        ),
    ] = False,
) -> None:
    state = _state(ctx)
    visibility = _resolve_visibility(
        include_drafts=include_drafts,
        include_superseded=include_superseded,
        all_statuses=all_statuses,
    )

    def _build_changed_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        repo.status()
        if not config.tracking_enabled:
            raise StorageError(
                "Source tracking is disabled by [tracking].enabled = false."
            )
        from archledger.source_tracking import (
            scan_git_revision,
            scan_since_merge_base,
        )

        if since_merge_base is not None:
            base_state, current = scan_since_merge_base(paths, config, since_merge_base)
            changes = diff_source_states(base_state, current)
        elif against is not None:
            base_state = scan_git_revision(
                paths, config, against, reason=f"git:{against}"
            )
            current = scan_workspace(paths, config, reason="current-scan")
            changes = diff_source_states(base_state, current)
        else:
            baseline = _load_tracking_baseline(paths, config)
            current = scan_workspace(paths, config, reason="current-scan")
            changes = diff_source_states(baseline, current)
        changes = resolve_impacts(
            repo.load_all_records(include_sections=True),
            changes,
            include_draft=visibility.include_drafts,
            include_superseded=visibility.include_superseded,
        )
        payload = _changed_payload(paths, changes, config)
        if fail_on_unlinked and changes.unlinked_changed_files:
            raise ArchledgerError(
                f"{len(changes.unlinked_changed_files)} unlinked changed file(s).",
                details=payload,
            )
        return payload

    _run_configured_command(
        state,
        "source changed",
        _build_changed_result,
        _format_changed_message,
    )


@app.command()
def build(
    ctx: typer.Context,
    output: Annotated[Path | None, typer.Option("--output")] = None,
    format_names: Annotated[list[str] | None, typer.Option("--format")] = None,
    all_formats: Annotated[bool, typer.Option("--all-formats")] = False,
    include_drafts: Annotated[bool, typer.Option("--include-drafts")] = False,
    include_superseded: Annotated[bool, typer.Option("--include-superseded")] = False,
    all_statuses: Annotated[bool, typer.Option("--all-statuses")] = False,
    strict: Annotated[bool, typer.Option("--strict")] = False,
) -> None:
    state = _state(ctx)
    visibility = _resolve_visibility(
        include_drafts=include_drafts,
        include_superseded=include_superseded,
        all_statuses=all_statuses,
    )

    def _build_build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        result = build_document(
            repo,
            output=output,
            formats=tuple(format_names or ()),
            all_formats=all_formats,
            include_draft=visibility.include_drafts,
            include_superseded=visibility.include_superseded,
            strict=strict,
        )
        return _build_payload(result)

    _run_configured_command(state, "build", _build_build_result, _format_build_message)


@source_app.command("convert")
def convert_sources_command(
    ctx: typer.Context,
    to: Annotated[str, typer.Option("--to")] = "asciidoc",
    apply: Annotated[bool, typer.Option("--apply")] = False,
    replace: Annotated[bool, typer.Option("--replace")] = False,
    allow_mixed_body_format: Annotated[
        bool,
        typer.Option(
            "--allow-mixed-body-format",
            help=(
                "Allow writing .adoc files whose bodies remain Markdown when "
                "pandoc is unavailable."
            ),
        ),
    ] = False,
) -> None:
    state = _state(ctx)

    def _build_convert_sources_command_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo
        result = convert_sources(
            paths,
            config,
            target_format=to,
            write=apply,
            replace=replace,
            allow_mixed_body_format=allow_mixed_body_format,
        )
        return _convert_sources_payload(result)

    _run_configured_command(
        state,
        "source convert",
        _build_convert_sources_command_result,
        _format_convert_sources_message,
    )


@app.command("context")
def context_cmd(
    ctx: typer.Context,
    for_file: Annotated[str | None, typer.Option("--for-file")] = None,
    for_record: Annotated[str | None, typer.Option("--for-record")] = None,
    changed: Annotated[bool, typer.Option("--changed")] = False,
    topic: Annotated[str | None, typer.Option("--topic")] = None,
    include_body: Annotated[bool, typer.Option("--include-body")] = False,
    include_drafts: Annotated[bool, typer.Option("--include-drafts")] = False,
    include_superseded: Annotated[bool, typer.Option("--include-superseded")] = False,
    max_records: Annotated[int, typer.Option("--max-records")] = 20,
    max_per_category: Annotated[int, typer.Option("--max-per-category")] = 8,
    scope: Annotated[str | None, typer.Option("--scope")] = None,
    scope_kind: Annotated[str | None, typer.Option("--scope-kind")] = None,
    addon: Annotated[str | None, typer.Option("--addon")] = None,
) -> None:
    state = _state(ctx)

    # Mutually exclusive selectors
    selectors = [
        for_file is not None,
        for_record is not None,
        changed,
        topic is not None,
    ]
    if sum(selectors) > 1:
        raise ArchledgerError(
            "Specify only one of --topic, --for-file, --for-record, or --changed."
        )

    def _build_context(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        from archledger.context import (
            build_context_for_changed,
            build_context_for_file,
            build_context_for_record,
            build_context_for_topic,
        )

        if for_file is not None:
            return build_context_for_file(
                repo,
                for_file,
                config,
                include_body=include_body,
                max_records=max_records,
            )
        if for_record is not None:
            return build_context_for_record(
                repo,
                for_record,
                config,
                include_body=include_body,
                max_records=max_records,
            )
        if changed:
            from archledger.source_tracking import (
                diff_source_states,
                resolve_impacts,
                scan_workspace,
            )
            from archledger.storage.source_state import read_source_state

            baseline = read_source_state(paths.source_state_path)
            current = scan_workspace(paths, config, reason="context-changed")
            changes = diff_source_states(baseline, current)
            changes = resolve_impacts(
                repo.load_all_records(include_sections=True),
                changes,
                include_draft=False,
                include_superseded=False,
            )
            return build_context_for_changed(
                repo,
                changes,
                config,
                include_body=include_body,
                max_records=max_records,
            )
        if topic is not None:
            return build_context_for_topic(
                repo,
                topic,
                config,
                include_body=include_body,
                include_draft=include_drafts,
                include_superseded=include_superseded,
                max_records=max_records,
                max_per_category=max_per_category,
                scope=scope,
                scope_kind=scope_kind,
                addon=addon,
            )
        raise ArchledgerError(
            "Specify --topic, --for-file, --for-record, or --changed."
        )

    def _format_context(payload: dict[str, object]) -> str:
        records = payload.get("records", [])
        categories = payload.get("categories")
        if isinstance(categories, dict):
            total = sum(len(v) for v in categories.values() if isinstance(v, list))
            return f"Topic context: {total} categorized record(s)."
        if isinstance(records, list):
            return f"Context: {len(records)} record(s)."
        return "Context: no records."

    _run_configured_command(state, "context", _build_context, _format_context)


@app.command("trace")
def trace_cmd(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: trace-json or combo-json."),
    ] = "trace-json",
) -> None:
    state = _state(ctx)

    def _build_trace(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths
        from archledger.trace import build_trace

        trace_payload = build_trace(repo, record_id, config)
        if output_format == "combo-json":
            from archledger.combo_trace import build_combo_trace

            return build_combo_trace(trace_payload)
        if output_format != "trace-json":
            raise ArchledgerError("--format must be trace-json or combo-json.")
        return trace_payload

    def _format_trace(payload: dict[str, object]) -> str:
        if payload.get("schema") == "combi.trace.v1":
            subject = payload.get("subject")
            if isinstance(subject, dict):
                return f"Combo trace for {subject.get('id')}"
            return "Combo trace complete."
        root = payload.get("root")
        if root is None:
            return str(payload.get("error", "Record not found."))
        if isinstance(root, dict):
            return f"Trace for {root.get('id')}: {root.get('title')}"
        return "Trace complete."

    _run_configured_command(state, "trace", _build_trace, _format_trace)


@record_app.command("set")
def record_set_status(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    status: Annotated[str | None, typer.Argument(help="New status.")] = None,
    legacy_status: Annotated[
        str | None, typer.Option("--status", help="New status (legacy syntax).")
    ] = None,
    reason: Annotated[
        str, typer.Option("--reason", help="Reason for the change.")
    ] = "",
) -> None:
    state = _state(ctx)
    set_status = status or legacy_status or ""
    if not set_status:
        raise ArchledgerError("--status is required.")

    def _mutate(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
        target_path: Path,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import set_record_status as _set_status

        _set_status(
            target_path,
            record_id,
            set_status,
            workspace_root=paths.workspace_root,
        )
        return {
            "id": record_id,
            "path": str(target_path),
            "status": set_status,
            "reason": reason,
        }

    def _fmt(p: dict[str, object]) -> str:
        return f"Set {p.get('id')} status to {p.get('status')}."

    canonical = ctx.command.name == "set-status"
    _run_record_mutation(
        state,
        "record set-status" if canonical else "record set",
        record_id,
        _mutate,
        _fmt,
        extra_warnings=[]
        if canonical
        else [
            {
                "code": "deprecated_command",
                "message": (
                    "`archledger record set` is deprecated; use `archledger record "
                    "set-status` instead."
                ),
                "replacement": "record set-status",
            }
        ],
    )


record_app.command("set-status")(record_set_status)


@record_app.command("export")
def record_export(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            dir_okay=False,
            resolve_path=True,
            help="Write the record document to this path.",
        ),
    ],
) -> None:
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        from archledger.mutations import export_record_document

        target_path = _find_record_path(repo, record_id)
        write_text_atomic(output, export_record_document(target_path, record_id))
        return {"id": record_id, "output_path": str(output), "path": str(target_path)}

    _run_configured_command(
        state,
        "record export",
        _build,
        lambda payload: (
            f"Exported {payload.get('id')} to {payload.get('output_path')}."
        ),
    )


@record_app.command("apply")
def record_apply(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    from_file: Annotated[
        Path,
        typer.Option(
            "--from-file",
            exists=True,
            dir_okay=False,
            resolve_path=True,
            help="Read the replacement record document from this file.",
        ),
    ],
) -> None:
    state = _state(ctx)

    def _mutate(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
        target_path: Path,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import apply_record_document

        before = target_path.read_text(encoding="utf-8")
        apply_record_document(
            target_path,
            record_id,
            from_file.read_text(encoding="utf-8"),
            workspace_root=paths.workspace_root,
        )
        after = target_path.read_text(encoding="utf-8")
        return {
            "id": record_id,
            "path": str(target_path),
            "changed": before != after,
            "source_path": str(from_file),
        }

    def _fmt(payload: dict[str, object]) -> str:
        if payload.get("changed"):
            return (
                f"Applied record document from {payload.get('source_path')} "
                f"to {payload.get('id')}."
            )
        return f"No changes applied to {payload.get('id')}."

    _run_record_mutation(state, "record apply", record_id, _mutate, _fmt)


@record_meta_app.command("set")
def record_meta_set(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    key: Annotated[str, typer.Argument()],
    value: Annotated[
        str | None,
        typer.Argument(
            help="Positional value; parsed as JSON when possible for compatibility.",
            show_default=False,
        ),
    ] = None,
    json_value: Annotated[
        str | None,
        typer.Option(
            "--json-value",
            help="Parse this JSON value literally.",
        ),
    ] = None,
    string_value: Annotated[
        str | None,
        typer.Option(
            "--string-value",
            help="Store this value as a raw string.",
        ),
    ] = None,
    from_file: Annotated[
        Path | None,
        typer.Option(
            "--from-file",
            exists=True,
            dir_okay=False,
            resolve_path=True,
            help="Parse one YAML or JSON value from this file.",
        ),
    ] = None,
) -> None:
    state = _state(ctx)
    metadata_value = _resolve_record_meta_value(
        value=value,
        json_value=json_value,
        string_value=string_value,
        from_file=from_file,
    )

    def _mutate(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
        target_path: Path,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import set_record_meta

        set_record_meta(
            target_path,
            record_id,
            key,
            metadata_value,
            workspace_root=paths.workspace_root,
        )
        return {"id": record_id, "path": str(target_path), "key": key}

    _run_record_mutation(
        state,
        "record meta set",
        record_id,
        _mutate,
        lambda payload: f"Set {payload.get('id')} metadata {payload.get('key')}.",
    )


@record_body_app.command("append")
def record_body_append(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False)],
) -> None:
    state = _state(ctx)

    def _mutate(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
        target_path: Path,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import append_record_body

        append_record_body(
            target_path,
            record_id,
            file.read_text(encoding="utf-8"),
            workspace_root=paths.workspace_root,
        )
        return {"id": record_id, "path": str(target_path)}

    _run_record_mutation(
        state,
        "record body append",
        record_id,
        _mutate,
        lambda payload: f"Appended body content to {payload.get('id')}.",
    )


@record_body_app.command("set")
def record_body_set(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    from_file: Annotated[
        Path | None,
        typer.Option(
            "--from-file",
            exists=True,
            dir_okay=False,
            help="Replace the record body with the contents of this file.",
        ),
    ] = None,
    text: Annotated[
        str | None,
        typer.Option("--text", help="Replace the record body with this text."),
    ] = None,
) -> None:
    """Replace a record body (removing the template placeholder)."""
    state = _state(ctx)
    if (from_file is None) == (text is None):
        raise ArchledgerError("Provide exactly one of --from-file or --text.")

    def _mutate(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
        target_path: Path,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import replace_record_body

        body_text = (
            from_file.read_text(encoding="utf-8")
            if from_file is not None
            else (text or "")
        )
        replace_record_body(
            target_path,
            record_id,
            body_text,
            workspace_root=paths.workspace_root,
        )
        return {"id": record_id, "path": str(target_path)}

    _run_record_mutation(
        state,
        "record body set",
        record_id,
        _mutate,
        lambda payload: f"Replaced body of {payload.get('id')}.",
    )


@refs_app.command("add")
def refs_add(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    path: Annotated[str, typer.Option("--path", help="Source file path.")] = "",
    role: Annotated[str, typer.Option("--role", help="Source ref role.")] = "",
    reason: Annotated[str, typer.Option("--reason", help="Reason.")] = "",
) -> None:
    state = _state(ctx)
    if not path:
        raise ArchledgerError("--path is required.")

    def _mutate(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
        target_path: Path,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import add_source_ref as _add_ref

        _add_ref(
            target_path,
            record_id,
            path,
            role=role,
            reason=reason,
            workspace_root=paths.workspace_root,
        )
        return {"id": record_id, "path": str(target_path), "ref": path}

    def _fmt(p: dict[str, object]) -> str:
        return f"Added source_ref to {p.get('id')}: {p.get('ref')}."

    canonical = ctx.parent is not None and ctx.parent.command.name == "ref"
    _run_record_mutation(
        state,
        "ref add" if canonical else "refs add",
        record_id,
        _mutate,
        _fmt,
        extra_warnings=[]
        if canonical
        else [
            {
                "code": "deprecated_command",
                "message": (
                    "`archledger refs` is deprecated; use `archledger ref` instead."
                ),
                "replacement": "ref",
            }
        ],
    )


ref_app.command("add")(refs_add)


@links_app.command("add")
def links_add(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    rel: Annotated[str, typer.Option("--rel", help="Link relationship.")] = "",
    target: Annotated[str, typer.Option("--target", help="Target record ID.")] = "",
    reason: Annotated[str, typer.Option("--reason", help="Reason.")] = "",
) -> None:
    state = _state(ctx)
    if not rel or not target:
        raise ArchledgerError("--rel and --target are required.")

    def _mutate(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
        target_path: Path,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import add_link as _add_link

        _add_link(
            target_path,
            record_id,
            rel,
            target,
            reason=reason,
            workspace_root=paths.workspace_root,
        )
        return {
            "id": record_id,
            "path": str(target_path),
            "rel": rel,
            "target": target,
        }

    def _fmt(p: dict[str, object]) -> str:
        return f"Added link {p.get('rel')} -> {p.get('target')} to {p.get('id')}."

    canonical = ctx.parent is not None and ctx.parent.command.name == "link"
    _run_record_mutation(
        state,
        "link add" if canonical else "links add",
        record_id,
        _mutate,
        _fmt,
        extra_warnings=[]
        if canonical
        else [
            {
                "code": "deprecated_command",
                "message": (
                    "`archledger links` is deprecated; use `archledger link` instead."
                ),
                "replacement": "link",
            }
        ],
    )


link_app.command("add")(links_add)


class _ScopeEntry(TypedDict):
    name: str
    kind: str
    lifecycle: str
    applies_to: list[str]
    excludes: list[str]
    records: list[str]


class _ScopeSummary(TypedDict):
    name: str
    kind: str
    lifecycle: str
    applies_to: list[str]
    excludes: list[str]


class _ScopeRecord(TypedDict):
    id: str
    type: str
    title: str
    scope_name: str


class _ScopeShowRecord(TypedDict):
    id: str
    type: str
    title: str


@scope_app.command("list")
def scope_list(
    ctx: typer.Context,
) -> None:
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        scopes: dict[str, _ScopeEntry] = {}
        for record in repo.load_all_records(include_sections=True):
            if record.scope is None:
                continue
            s = record.scope
            if s.name not in scopes:
                scopes[s.name] = {
                    "name": s.name,
                    "kind": s.kind,
                    "lifecycle": s.lifecycle,
                    "applies_to": list(s.applies_to),
                    "excludes": list(s.excludes),
                    "records": [],
                }
            scopes[s.name]["records"].append(record.id)
        return {"scopes": list(scopes.values())}

    def _fmt(p: dict[str, object]) -> str:
        raw_scopes = cast("list[object]", p.get("scopes", []))
        if not raw_scopes:
            return "No scopes defined."
        lines: list[str] = []
        for item in raw_scopes:
            if isinstance(item, dict):
                entry = cast("_ScopeEntry", item)
                lines.append(
                    f"  {entry['name']} (kind={entry['kind']}, "
                    f"lifecycle={entry['lifecycle']}, "
                    f"records={len(entry['records'])})"
                )
        return "Scopes:\n" + "\n".join(lines)

    _run_configured_command(state, "scope list", _build, _fmt)


@scope_app.command("show")
def scope_show(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Scope name.")],
) -> None:
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        matched_records: list[_ScopeShowRecord] = []
        scope_obj = None
        for record in repo.load_all_records(include_sections=True):
            if record.scope is not None and record.scope.name == name:
                scope_obj = record.scope
                matched_records.append(
                    {"id": record.id, "type": record.type, "title": record.title}
                )
        if scope_obj is None:
            return {"error": f"No scope named {name!r} found."}
        return {
            "scope": {
                "name": scope_obj.name,
                "kind": scope_obj.kind,
                "lifecycle": scope_obj.lifecycle,
                "applies_to": list(scope_obj.applies_to),
                "excludes": list(scope_obj.excludes),
            },
            "records": matched_records,
        }

    def _fmt(p: dict[str, object]) -> str:
        if "error" in p:
            return str(p["error"])
        raw_scope = p.get("scope", {})
        if not isinstance(raw_scope, dict):
            return "Malformed scope payload."
        scope_data = cast("_ScopeSummary", raw_scope)
        lines = [
            f"Scope: {scope_data['name']}",
            f"  Kind: {scope_data['kind']}",
            f"  Lifecycle: {scope_data['lifecycle']}",
            f"  Applies to: {', '.join(scope_data['applies_to'])}",
            f"  Excludes: {', '.join(scope_data['excludes']) or '(none)'}",
            "  Records:",
        ]
        show_records = cast("list[object]", p.get("records", []))
        for r in show_records:
            if isinstance(r, dict):
                lines.append(f"    {r.get('id')}: {r.get('title')} ({r.get('type')})")
        return "\n".join(lines)

    _run_configured_command(state, "scope show", _build, _fmt)


@scope_app.command("affected")
def scope_affected(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="File or directory path to check.")],
) -> None:
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        from archledger.scopes import scope_matches_path

        normalized_path = path.replace("\\", "/").strip()
        affected: list[_ScopeRecord] = []
        for record in repo.load_all_records(include_sections=True):
            if record.scope is None:
                continue
            if scope_matches_path(record.scope, normalized_path):
                affected.append(
                    {
                        "id": record.id,
                        "type": record.type,
                        "title": record.title,
                        "scope_name": record.scope.name,
                    }
                )
        return {"path": normalized_path, "affected_records": affected}

    def _fmt(p: dict[str, object]) -> str:
        records = cast("list[object]", p.get("affected_records", []))
        if not records:
            return f"No scoped records affected for {p.get('path')}."
        lines = [f"Scoped records affected by {p.get('path')}:"]
        for item in records:
            if isinstance(item, dict):
                rec = cast("_ScopeRecord", item)
                lines.append(
                    f"  {rec['id']}: {rec['title']} "
                    f"(scope={rec['scope_name']}, {rec['type']})"
                )
        return "\n".join(lines)

    _run_configured_command(state, "scope affected", _build, _fmt)


@ac_app.command("add")
def acceptance_criterion_add(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    statement: Annotated[str, typer.Option("--statement")],
    command: Annotated[str, typer.Option("--command")] = "",
    expected: Annotated[str, typer.Option("--expected")] = "passes",
) -> None:
    state = _state(ctx)

    def _mutate(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
        target_path: Path,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import add_acceptance_criterion

        add_acceptance_criterion(
            target_path,
            record_id,
            statement,
            validation_command=command,
            expected=expected,
            workspace_root=paths.workspace_root,
        )
        return {"id": record_id, "path": str(target_path)}

    _run_record_mutation(
        state,
        "ac add",
        record_id,
        _mutate,
        lambda payload: f"Added acceptance criterion to {payload.get('id')}.",
    )


def _find_record_path(repo: ArchitectureRepository, record_id: str) -> Path:
    record = repo.get_record(record_id)
    return record.path


def _run_record_mutation(
    state: CommonCLIState,
    command: str,
    record_id: str,
    payload_builder: Callable[
        [ArchitectureRepository, ProjectPaths, ProjectConfig, Path],
        dict[str, object],
    ],
    human_formatter: Callable[[dict[str, object]], str],
    extra_warnings: list[object] | None = None,
) -> None:
    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        target_path = _find_record_path(repo, record_id)
        original_text = target_path.read_text(encoding="utf-8")
        try:
            payload = payload_builder(repo, paths, config, target_path)
            _validate_mutation(repo, target_path)
            return payload
        except ArchledgerError:
            _restore_record_text(target_path, original_text)
            raise

    _run_configured_command(
        state,
        command,
        _build,
        human_formatter,
        extra_warnings=extra_warnings,
    )


def _restore_record_text(path: Path, original_text: str) -> None:
    write_text_atomic(path, original_text)


def _parse_cli_value(value: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _resolve_record_meta_value(
    *,
    value: str | None,
    json_value: str | None,
    string_value: str | None,
    from_file: Path | None,
) -> object:
    provided_sources = [
        value is not None,
        json_value is not None,
        string_value is not None,
        from_file is not None,
    ]
    if sum(provided_sources) != 1:
        raise ArchledgerError(
            "Provide exactly one of VALUE, --json-value, "
            "--string-value, or --from-file."
        )
    if json_value is not None:
        try:
            return json.loads(json_value)
        except json.JSONDecodeError as exc:
            raise ArchledgerError(f"Invalid JSON for --json-value: {exc.msg}") from exc
    if string_value is not None:
        return string_value
    if from_file is not None:
        try:
            return yaml.safe_load(from_file.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ArchledgerError(
                f"Invalid YAML or JSON in {from_file}: {exc}"
            ) from exc
    assert value is not None
    return _parse_cli_value(value)


def _validate_mutation(repo: ArchitectureRepository, path: Path) -> None:
    result = repo.check()
    errors = [
        finding.message
        for finding in result.errors
        if finding.path is not None and finding.path.resolve() == path.resolve()
    ]
    if errors:
        raise ArchledgerError(
            "Mutation produced an invalid record: " + "; ".join(errors)
        )


@app.command("install")
def install_scaffold_command(
    ctx: typer.Context,
    target: Annotated[str, typer.Argument()],
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    state = _state(ctx)
    try:
        from archledger.installers import install_scaffold

        result = install_scaffold(state.root, target, force=force)
        payload = {
            "target": result.target,
            "path": str(result.path),
            "overwritten": result.overwritten,
        }
        _emit_success(
            state,
            command="install",
            result=payload,
            warnings=[],
            human_message=f"Installed {result.target}: {result.path}",
        )
    except ArchledgerError as exc:
        _emit_error(state, "install", exc)


@profile_app.command("list")
def profile_list(ctx: typer.Context) -> None:
    state = _state(ctx)

    def _build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo, config
        from archledger.profiles import list_profiles as _list_profiles

        return _list_profiles(paths.config_path, paths.archledger_dir)

    _run_configured_command(
        state, "profile list", _build_result, _format_profile_list_message
    )


@profile_app.command("enable")
def profile_enable(
    ctx: typer.Context,
    profile: Annotated[str, typer.Argument()],
    write: Annotated[bool, typer.Option("--write")] = True,
) -> None:
    state = _state(ctx)

    def _build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo, config
        from archledger.profiles import enable_profile as _enable_profile

        result = _enable_profile(
            paths.config_path, paths.archledger_dir, profile, write=write
        )
        return _profile_migration_payload(result)

    _run_configured_command(
        state, "profile enable", _build_result, _format_profile_migration_message
    )


@profile_app.command("disable")
def profile_disable(
    ctx: typer.Context,
    profile: Annotated[str, typer.Argument()],
    write: Annotated[bool, typer.Option("--write")] = True,
) -> None:
    state = _state(ctx)

    def _build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo, config
        from archledger.profiles import disable_profile as _disable_profile

        result = _disable_profile(paths.config_path, profile, write=write)
        return _profile_migration_payload(result)

    _run_configured_command(
        state, "profile disable", _build_result, _format_profile_migration_message
    )


@profile_app.command("migrate")
def profile_migrate(
    ctx: typer.Context,
    profile: Annotated[str, typer.Argument()],
    write: Annotated[bool, typer.Option("--write")] = False,
) -> None:
    state = _state(ctx)

    def _build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo, config
        if profile != "arc42":
            raise ArchledgerError("Only arc42 profile migration is supported.")
        from archledger.profiles import migrate_arc42_profile as _migrate

        result = _migrate(paths.config_path, paths.archledger_dir, write=write)
        return _profile_migration_payload(result)

    _run_configured_command(
        state, "profile migrate", _build_result, _format_profile_migration_message
    )


def _run_configured_command(
    state: CommonCLIState,
    command: str,
    payload_builder: Callable[
        [ArchitectureRepository, ProjectPaths, ProjectConfig],
        dict[str, object],
    ],
    human_formatter: Callable[[dict[str, object]], str],
    extra_warnings: list[object] | None = None,
) -> None:
    try:
        paths, config, warnings = resolve_project_paths(state.root)
        if extra_warnings:
            warnings = list(warnings) + extra_warnings
        repo = ArchitectureRepository(paths, config)
        payload = payload_builder(repo, paths, config)
        _emit_success(
            state,
            command=command,
            result=payload,
            warnings=warnings,
            human_message=human_formatter(payload),
        )
    except ArchledgerError as exc:
        _emit_error(state, command, exc)


def _build_storage_where_output(root: Path) -> tuple[dict[str, object], str]:
    """Build storage where payload and human message from the adapter."""
    from archledger.cli_formatting import format_storage_where_message
    from archledger.cli_payloads import storage_where_payload
    from archledger.ledgercore_backend import load_archledger_layout

    layout = load_archledger_layout(root, require_registration=False)
    payload = storage_where_payload(layout)
    msg = format_storage_where_message(payload)
    return payload, msg


def _basic_workspace_state(root: Path, classification: str) -> dict[str, object]:
    """Build a read-only status payload without requiring initialization."""
    manifest_path = root.resolve(strict=False) / ".ledger" / "ledger.toml"
    registered = False
    effective_registration_present = False
    tool_config_exists = False
    data_root_exists = False
    project_uuid: str | None = None
    try:
        from archledger.ledgercore_backend import load_archledger_layout

        layout = load_archledger_layout(root, require_registration=False)
        effective_registration_present = layout.raw_effective is not None
        registered = effective_registration_present
        tool_config_exists = layout.tool_config_path.exists()
        data_root_exists = layout.data_root.exists()
        project_uuid = layout.project_uuid
    except Exception:
        pass
    next_actions = {
        "uninitialized": "archledger init",
        "legacy": "archledger migrate plan project-layout",
        "partial": "archledger storage validate --strict",
        "invalid": "archledger doctor",
    }
    return {
        "state": classification,
        "project_root": str(root.resolve(strict=False)),
        "registered": registered,
        "effective_registration_present": effective_registration_present,
        "initialized": classification == "canonical",
        "valid": classification == "canonical",
        "record_count": 0,
        "draft_count": 0,
        "migration_state": classification,
        "recommended_next": next_actions.get(classification, "archledger status"),
        "manifest_path": str(manifest_path),
        "tool_config_exists": tool_config_exists,
        "data_root_exists": data_root_exists,
        "project_uuid": project_uuid,
    }


def _trusted_migration_paths(root: Path) -> list[str]:
    """List only regular migration journal paths under the project directory."""
    directory = root.resolve(strict=False) / ".ledger" / "migrations"
    if not directory.is_dir():
        return []
    return [
        str(path)
        for path in sorted(directory.glob("*.toml"))
        if path.is_file() and not path.is_symlink()
    ]


def _load_tracking_baseline(
    paths: ProjectPaths,
    config: ProjectConfig,
) -> SourceState | None:
    state = read_source_state(paths.source_state_path)
    if state is None:
        return None
    if state.project_uuid != config.project_uuid:
        raise StorageError(
            "source-state project_uuid does not match the "
            "current project configuration."
        )
    return state


def _state(ctx: typer.Context) -> CommonCLIState:
    state = ctx.obj
    if not isinstance(state, CommonCLIState):
        raise RuntimeError("CLI state was not initialized.")
    return state


def _run_simple_command(
    ctx: typer.Context,
    command: str,
    payload_builder: Callable[
        [ArchitectureRepository, ProjectPaths, ProjectConfig],
        dict[str, object],
    ],
    human_formatter: Callable[[dict[str, object]], str],
) -> None:
    _run_configured_command(_state(ctx), command, payload_builder, human_formatter)


def _check_error(result: CheckResult, *, strict: bool) -> ArchledgerError:
    summary = (
        f"Check failed with {len(result.errors)} error(s) and "
        f"{len(result.warnings)} warning(s)."
    )
    return ArchledgerError(
        summary,
        details={
            "strict": strict,
            "errors": [_finding_payload(finding) for finding in result.errors],
            "warnings": [_finding_payload(finding) for finding in result.warnings],
        },
    )


def _seed_arc42_minimal(repo: ArchitectureRepository) -> list[ArchitectureRecord]:
    created_records = [
        repo.create_record("white-box", "Overall System", status="proposed"),
        repo.create_record("quality-goal", "Maintainability", status="proposed"),
        repo.create_record("quality-goal", "Traceability", status="proposed"),
        repo.create_record("quality-goal", "Reproducibility", status="proposed"),
        repo.create_record("stakeholder", "Developer", status="proposed"),
        repo.create_record("stakeholder", "Architect", status="proposed"),
        repo.create_record(
            "constraint",
            "Markdown as source format",
            status="proposed",
        ),
        repo.create_record(
            "context-interface",
            "Source repository",
            status="proposed",
            context_kind="technical",
            partner="Source repository",
        ),
        repo.create_record(
            "adr",
            "Use Markdown records with YAML front matter",
            status="proposed",
        ),
        repo.create_record(
            "risk",
            "Documentation can drift from implementation",
            status="proposed",
        ),
        repo.create_record("glossary-term", "Architecture Record", status="proposed"),
    ]
    return created_records
