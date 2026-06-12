from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Annotated

import typer

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
    format_paths_message as _format_paths_message,
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
from archledger.cli_payloads import (
    where_payload as _where_payload,
)
from archledger.errors import ArchledgerError, StorageError
from archledger.id_format_drift import find_id_format_drift
from archledger.identity_migration import migrate_identity
from archledger.ids import DEFAULT_ID_PREFIX, DEFAULT_ID_SEGMENT_MODE, DEFAULT_ID_WIDTH
from archledger.migration import convert_sources
from archledger.model import ArchitectureRecord, known_source_extensions
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
    CANONICAL_PROJECT_CONFIG_FILENAME,
    DEFAULT_ARCHLEDGER_DIR_NAME,
    HIDDEN_PROJECT_CONFIG_FILENAME,
    ProjectPaths,
    resolve_project_paths,
)
from archledger.storage.project_config import (
    ProjectConfig,
    build_default_project_config,
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
ac_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(ac_app, name="ac", help="Manage inline acceptance criteria.")
scope_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(scope_app, name="scope", help="Inspect record scope metadata.")


@dataclass(frozen=True, slots=True)
class CLIState:
    root: Path
    json_output: bool


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
    ctx.obj = CLIState(
        root=Path.cwd() if root is None else root,
        json_output=json_output,
    )


@app.command()
def init(
    ctx: typer.Context,
    archledger_dir: Annotated[
        str,
        typer.Option(
            "--archledger-dir",
            help=(
                "State directory to create, relative to the config path unless "
                "absolute."
            ),
        ),
    ] = DEFAULT_ARCHLEDGER_DIR_NAME,
    project_name: Annotated[
        str | None,
        typer.Option(
            "--project-name",
            help="Stable project identity stored in archledger.toml.",
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
    config_path = workspace_root / CANONICAL_PROJECT_CONFIG_FILENAME
    hidden_config_path = workspace_root / HIDDEN_PROJECT_CONFIG_FILENAME
    existing_configs = [
        path for path in (config_path, hidden_config_path) if path.exists()
    ]
    if existing_configs:
        _emit_error(
            state,
            "init",
            ArchledgerError(
                "Config file already exists: "
                + ", ".join(str(path) for path in existing_configs)
            ),
        )
    try:
        opts = InitOptions(
            archledger_dir=archledger_dir,
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
        config = build_default_project_config(
            workspace_root,
            archledger_dir=opts.archledger_dir,
            source_format=opts.source_format,
            id_prefix=opts.id_prefix,
            id_width=opts.id_width,
            id_segment_mode=opts.id_segment_mode,
            profile=opts.profile,
            extra_profiles=opts.extra_profiles,
            project_name=opts.project_name,
            project_uuid=opts.project_uuid,
            build_default_format=opts.build.default_format,
            build_default_output=opts.build.default_output,
            build_default_output_dir=opts.build.default_output_dir,
            build_include_draft=opts.build.include_draft,
            build_include_superseded=opts.build.include_superseded,
            build_strict=opts.build.strict,
            build_keep_intermediate=opts.build.keep_intermediate,
            build_converter=opts.build.converter,
            build_pdf_engine=opts.build.pdf_engine,
            build_reference_docx=opts.build.reference_docx,
            diagram_enabled=opts.diagrams.enabled,
            diagram_renderer=opts.diagrams.renderer,
            diagram_default_type=opts.diagrams.default_type,
            diagram_output_dir=opts.diagrams.output_dir,
            diagram_image_format=opts.diagrams.image_format,
            diagram_kroki_url=opts.diagrams.kroki_url,
            arc42_title=opts.arc42.title,
            arc42_language=opts.arc42.language,
            arc42_template_version=opts.arc42.template_version,
            arc42_include_help=opts.arc42.include_help,
            tracking_enabled=opts.tracking.enabled,
            tracking_scanner=opts.tracking.scanner,
            tracking_state_file=opts.tracking.state_file,
            tracking_max_file_bytes=opts.tracking.max_file_bytes,
            tracking_include=opts.tracking.include or None,
            tracking_exclude=opts.tracking.exclude or None,
        )
        from archledger.config.render import render_project_config as _render

        config_text = _render(config)
        write_text_atomic(config_path, config_text)
        paths, resolved_config, warnings = resolve_project_paths(workspace_root)
        repo = ArchitectureRepository(paths, resolved_config)
        result = repo.init()
        payload = _init_payload(result)
        _emit_success(
            state,
            command="init",
            result=payload,
            warnings=warnings,
            human_message=_format_init_message(payload),
        )
    except ArchledgerError as exc:
        _emit_error(state, "init", exc)


@app.command()
def status(ctx: typer.Context) -> None:
    _run_simple_command(ctx, "status", _status_payload, _format_status_message)


@app.command("paths")
def paths(ctx: typer.Context) -> None:
    _run_simple_command(ctx, "paths", _where_payload, _format_paths_message)


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
        del paths, config
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
            )
        )

    _run_configured_command(state, "new", _build_new_record_result, _format_new_message)


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
        del paths, config
        if preset == "arc42-minimal":
            records = _seed_arc42_minimal(repo)
        else:
            raise ArchledgerError(f"Unsupported seed preset: {preset}")
        return _seed_payload(preset, records)

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
        del paths, config
        return _list_payload(
            repo.list_records(
                include_draft=visibility.include_drafts,
                include_superseded=visibility.include_superseded,
                kind=kind,
                scope=scope,
            )
        )

    _run_configured_command(
        state, "list", _build_list_records_result, _format_list_message
    )


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
        del paths, config
        return _show_payload(repo.get_record(record_id))

    _run_configured_command(state, "show", _build_show_result, _format_show_message)


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

    _run_configured_command(state, "read", _build_read_result, _format_read_message)


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

    _run_configured_command(
        state, "archive", _build_archive_result, _format_archive_message
    )


@app.command("doctor")
def doctor(
    ctx: typer.Context,
    repair: Annotated[bool, typer.Option("--repair")] = False,
) -> None:
    state = _state(ctx)

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
                f"Identity migration applied: {payload.get('migrated_count', 0)} file(s) "
                f"({payload.get('rewritten_count', 0)} rewritten)."
            )
        )

    _run_configured_command(state, "migrate ids", _build_migrate_result, _fmt)


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
        scanned_state = scan_workspace(paths, config, reason=reason)
        if existing_state is not None:
            scanned_state = replace(scanned_state, created_at=existing_state.created_at)
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
        payload = _changed_payload(paths, changes)
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
                repo, for_file, include_body=include_body, max_records=max_records
            )
        if for_record is not None:
            return build_context_for_record(
                repo, for_record, include_body=include_body, max_records=max_records
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
                repo, changes, include_body=include_body, max_records=max_records
            )
        if topic is not None:
            return build_context_for_topic(
                repo,
                topic,
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
        del paths, config
        from archledger.trace import build_trace

        trace_payload = build_trace(repo, record_id)
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
    set_status: Annotated[str, typer.Option("--status", help="New status.")] = "",
) -> None:
    state = _state(ctx)
    if not set_status:
        raise ArchledgerError("--status is required.")

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import set_record_status as _set_status

        target_path = _find_record_path(repo, record_id)
        _set_status(
            target_path,
            record_id,
            set_status,
            workspace_root=paths.workspace_root,
        )
        _validate_mutation(repo, target_path)
        return {"id": record_id, "path": str(target_path), "status": set_status}

    def _fmt(p: dict[str, object]) -> str:
        return f"Set {p.get('id')} status to {p.get('status')}."

    _run_configured_command(state, "record set", _build, _fmt)


@record_meta_app.command("set")
def record_meta_set(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    key: Annotated[str, typer.Argument()],
    value: Annotated[str, typer.Argument()],
) -> None:
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import set_record_meta

        target_path = _find_record_path(repo, record_id)
        set_record_meta(
            target_path,
            record_id,
            key,
            _parse_cli_value(value),
            workspace_root=paths.workspace_root,
        )
        _validate_mutation(repo, target_path)
        return {"id": record_id, "path": str(target_path), "key": key}

    _run_configured_command(
        state,
        "record meta set",
        _build,
        lambda payload: f"Set {payload.get('id')} metadata {payload.get('key')}.",
    )


@record_body_app.command("append")
def record_body_append(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
    file: Annotated[Path, typer.Option("--file", exists=True, dir_okay=False)],
) -> None:
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import append_record_body

        target_path = _find_record_path(repo, record_id)
        append_record_body(
            target_path,
            record_id,
            file.read_text(encoding="utf-8"),
            workspace_root=paths.workspace_root,
        )
        _validate_mutation(repo, target_path)
        return {"id": record_id, "path": str(target_path)}

    _run_configured_command(
        state,
        "record body append",
        _build,
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

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import replace_record_body

        target_path = _find_record_path(repo, record_id)
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
        _validate_mutation(repo, target_path)
        return {"id": record_id, "path": str(target_path)}

    _run_configured_command(
        state,
        "record body set",
        _build,
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

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import add_source_ref as _add_ref

        target_path = _find_record_path(repo, record_id)
        _add_ref(
            target_path,
            record_id,
            path,
            role=role,
            reason=reason,
            workspace_root=paths.workspace_root,
        )
        _validate_mutation(repo, target_path)
        return {"id": record_id, "path": str(target_path), "ref": path}

    def _fmt(p: dict[str, object]) -> str:
        return f"Added source_ref to {p.get('id')}: {p.get('ref')}."

    _run_configured_command(state, "refs add", _build, _fmt)


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

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import add_link as _add_link

        target_path = _find_record_path(repo, record_id)
        _add_link(
            target_path,
            record_id,
            rel,
            target,
            reason=reason,
            workspace_root=paths.workspace_root,
        )
        _validate_mutation(repo, target_path)
        return {
            "id": record_id,
            "path": str(target_path),
            "rel": rel,
            "target": target,
        }

    def _fmt(p: dict[str, object]) -> str:
        return f"Added link {p.get('rel')} -> {p.get('target')} to {p.get('id')}."

    _run_configured_command(state, "links add", _build, _fmt)


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
        scopes: dict[str, dict[str, object]] = {}
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
            scopes[s.name]["records"].append(record.id)  # type: ignore[union-attr]
        return {"scopes": list(scopes.values())}

    def _fmt(p: dict[str, object]) -> str:
        scopes = p.get("scopes", [])
        if not scopes:
            return "No scopes defined."
        lines = []
        for s in scopes:
            if isinstance(s, dict):
                lines.append(
                    f"  {s.get('name')} (kind={s.get('kind')}, "
                    f"lifecycle={s.get('lifecycle')}, "
                    f"records={len(s.get('records', []))})"
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
        matched_records = []
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
        s = p.get("scope", {})
        lines = [
            f"Scope: {s.get('name')}",
            f"  Kind: {s.get('kind')}",
            f"  Lifecycle: {s.get('lifecycle')}",
            f"  Applies to: {', '.join(s.get('applies_to', []))}",
            f"  Excludes: {', '.join(s.get('excludes', [])) or '(none)'}",
            "  Records:",
        ]
        for r in p.get("records", []):
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
        affected = []
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
        records = p.get("affected_records", [])
        if not records:
            return f"No scoped records affected for {p.get('path')}."
        lines = [f"Scoped records affected by {p.get('path')}:"]
        for r in records:
            if isinstance(r, dict):
                lines.append(
                    f"  {r.get('id')}: {r.get('title')} "
                    f"(scope={r.get('scope_name')}, {r.get('type')})"
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

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import add_acceptance_criterion

        target_path = _find_record_path(repo, record_id)
        add_acceptance_criterion(
            target_path,
            record_id,
            statement,
            validation_command=command,
            expected=expected,
            workspace_root=paths.workspace_root,
        )
        _validate_mutation(repo, target_path)
        return {"id": record_id, "path": str(target_path)}

    _run_configured_command(
        state,
        "ac add",
        _build,
        lambda payload: f"Added acceptance criterion to {payload.get('id')}.",
    )


def _find_record_path(repo: ArchitectureRepository, record_id: str) -> Path:
    record = repo.get_record(record_id)
    return record.path


def _parse_cli_value(value: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


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
    state: CLIState,
    command: str,
    payload_builder: Callable[
        [ArchitectureRepository, ProjectPaths, ProjectConfig],
        dict[str, object],
    ],
    human_formatter: Callable[[dict[str, object]], str],
) -> None:
    try:
        paths, config, warnings = resolve_project_paths(state.root)
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


def _state(ctx: typer.Context) -> CLIState:
    state = ctx.obj
    if not isinstance(state, CLIState):
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


def _emit_success(
    state: CLIState,
    *,
    command: str,
    result: dict[str, object],
    warnings: list[str],
    human_message: str,
) -> None:
    if state.json_output:
        normalized_result = _normalize_json_paths(result)
        typer.echo(
            json.dumps(
                {
                    "ok": True,
                    "command": command,
                    "result": normalized_result,
                    "warnings": warnings,
                },
                indent=2,
                sort_keys=False,
            )
        )
        return

    typer.echo(human_message)
    for warning in warnings:
        typer.echo(f"warning: {warning}")


def _emit_error(state: CLIState, command: str, exc: ArchledgerError) -> None:
    if state.json_output:
        typer.echo(
            json.dumps(
                {
                    "ok": False,
                    "command": command,
                    "error": {
                        "type": exc.__class__.__name__,
                        "message": exc.message,
                        "details": exc.details,
                    },
                    "warnings": [],
                },
                indent=2,
                sort_keys=False,
            )
        )
    else:
        typer.echo(f"{exc.__class__.__name__}: {exc.message}", err=True)
    raise typer.Exit(code=1)


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


_JSON_PATH_KEYS = frozenset(
    {
        "workspace_root",
        "config_path",
        "archledger_dir",
        "sections_dir",
        "records_dir",
        "archive_dir",
        "build_dir",
        "storage_meta_path",
        "source_state_path",
        "assembled_path",
        "output_path",
        "source_path",
        "from",
        "to",
        "path",
        "created_paths",
    }
)


def _normalize_json_paths(value: object, *, key: str | None = None) -> object:
    if isinstance(value, dict):
        return {
            item_key: _normalize_json_paths(item_value, key=item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        if key in {"created_paths"}:
            return [_normalize_path_string(item) for item in value]
        return [_normalize_json_paths(item, key=key) for item in value]
    if isinstance(value, str) and key is not None and _looks_like_path_key(key):
        return _normalize_path_string(value)
    return value


def _looks_like_path_key(key: str) -> bool:
    return key in _JSON_PATH_KEYS or key.endswith("_path") or key.endswith("_dir")


def _normalize_path_string(value: object) -> object:
    if not isinstance(value, str):
        return value
    return value.replace("\\", "/")


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
