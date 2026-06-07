from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Annotated

import typer

from archledger import __version__
from archledger.bdd.cli import bdd_app as _bdd_app
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
    format_sdd_check_message as _format_sdd_check_message,
)
from archledger.cli_formatting import (
    format_sdd_status_message as _format_sdd_status_message,
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
    sdd_check_payload as _sdd_check_payload,
)
from archledger.cli_payloads import (
    sdd_status_payload as _sdd_status_payload,
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
from archledger.ids import DEFAULT_ID_PREFIX, DEFAULT_ID_SEGMENT_MODE, DEFAULT_ID_WIDTH
from archledger.migration import convert_sources
from archledger.model import ArchitectureRecord
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
profile_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(
    profile_app,
    name="profile",
    help="Manage archledger profiles (arc42, sdd).",
)
sdd_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(
    sdd_app,
    name="sdd",
    help="Validate SDD traceability contracts.",
)
sdd_policy_app = typer.Typer(add_completion=False, no_args_is_help=True)
sdd_app.add_typer(sdd_policy_app, name="policy", help="Show or set SDD policy flags.")
sdd_waive_app = typer.Typer(add_completion=False, no_args_is_help=True)
sdd_app.add_typer(sdd_waive_app, name="waive", help="Manage SDD rule waivers.")
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
# Register BDD sub-app from archledger.bdd.cli (logic lives in bdd package)
app.add_typer(
    _bdd_app,
    name="bdd",
    help="Import and export BDD/Gherkin behavior metadata.",
)


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
            help="Initial project profile (arc42 or sdd).",
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
    if config_path.exists():
        _emit_error(
            state,
            "init",
            ArchledgerError(f"Config file already exists: {config_path}"),
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
        elif preset == "sdd-minimal":
            records = _seed_sdd_minimal(repo)
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
) -> None:
    state = _state(ctx)

    def _build_renumber_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
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
            new_prefix=prefix,
            new_width=width,
            new_segment_mode=id_segment_mode,
            apply=apply,
        )
        return _renumber_payload(result)

    _run_configured_command(
        state,
        "renumber",
        _build_renumber_result,
        _format_renumber_message,
    )


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
    include_body: Annotated[bool, typer.Option("--include-body")] = False,
    max_records: Annotated[int, typer.Option("--max-records")] = 20,
) -> None:
    state = _state(ctx)

    def _build_context(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        from archledger.context import (
            build_context_for_changed,
            build_context_for_file,
            build_context_for_record,
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
            if baseline is None:
                raise ArchledgerError(
                    "No source baseline. Run: archledger source snapshot"
                )
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
        raise ArchledgerError("Specify --for-file, --for-record, or --changed.")

    def _format_context(payload: dict[str, object]) -> str:
        records = payload.get("records", [])
        if isinstance(records, list):
            return f"Context: {len(records)} record(s)."
        return "Context: no records."

    _run_configured_command(state, "context", _build_context, _format_context)


@app.command("trace")
def trace_cmd(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
) -> None:
    state = _state(ctx)

    def _build_trace(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        from archledger.trace import build_trace

        return build_trace(repo, record_id)

    def _format_trace(payload: dict[str, object]) -> str:
        root = payload.get("root")
        if root is None:
            return payload.get("error", "Record not found.")
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


def _enforce_sdd_profile_enabled(
    config: ProjectConfig,
    *,
    allow_without_profile: bool,
    reason: str | None,
) -> None:
    """Fail fast when the SDD profile is not enabled, unless explicitly waived."""
    if "sdd" in config.profiles.profiles.enabled:
        return
    if not allow_without_profile:
        raise ArchledgerError(
            "SDD profile is not enabled for this project.",
            details={
                "profile_enabled": False,
                "hint": (
                    "Run: archledger profile enable sdd — or pass "
                    '--allow-without-profile --reason "..." for ad-hoc linting.'
                ),
            },
        )
    if not reason or not reason.strip():
        raise ArchledgerError("--allow-without-profile requires a non-empty --reason.")


@sdd_app.command("init")
def sdd_init(
    ctx: typer.Context,
    seed: Annotated[
        str | None,
        typer.Option(
            "--seed",
            help="Seed minimal contract records after enabling (use 'minimal').",
        ),
    ] = None,
    strict_defaults: Annotated[
        bool,
        typer.Option(
            "--strict-defaults",
            help=(
                "Turn on stricter SDD policy: require BDD automation for "
                "accepted records."
            ),
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Plan without writing any changes."),
    ] = False,
) -> None:
    """Enable the SDD profile, ensure [profiles.sdd], and print policy."""
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo
        from archledger.config.parse import load_project_config
        from archledger.profiles import (
            SDD_POLICY_FIELDS,
            enable_profile,
            set_sdd_profile_policy,
        )
        from archledger.sdd import sdd_options_from_config

        steps: list[str] = []
        enabled_before = "sdd" in config.profiles.profiles.enabled
        if not enabled_before:
            enable_result = enable_profile(
                paths.config_path,
                paths.archledger_dir,
                "sdd",
                write=not dry_run,
            )
            steps.append(
                "enable SDD profile"
                if enable_result.changed
                else "SDD profile already enabled"
            )
        else:
            steps.append("SDD profile already enabled")

        overrides: dict[str, bool] = {}
        if strict_defaults:
            overrides["require_bdd_automation_for_accepted_records"] = True
        before_policy = {
            f: bool(getattr(config.profiles.sdd, f)) for f in SDD_POLICY_FIELDS
        }
        if overrides and not dry_run:
            set_sdd_profile_policy(
                paths.config_path,
                paths.archledger_dir,
                overrides,
            )
            config = load_project_config(paths.config_path)
        elif overrides and dry_run:
            steps.append("(dry-run) would apply strict-defaults")
        effective = sdd_options_from_config(config, strict=False)
        policy = {
            "require_acceptance_criteria": effective.require_acceptance_criteria,
            "require_implementation_refs": effective.require_implementation_refs,
            "require_test_refs": effective.require_test_refs,
            "require_bdd_gwt_for_behavior_records": (
                effective.require_bdd_gwt_for_behavior_records
            ),
            "require_bdd_automation_for_accepted_records": (
                effective.require_bdd_automation_for_accepted_records
            ),
        }

        seeded: list[dict[str, object]] = []
        if seed == "minimal":
            if dry_run:
                steps.append("(dry-run) would seed sdd-minimal")
            else:
                # Reload repo so it sees the enabled profile state.
                repo2 = ArchitectureRepository(paths, config)
                records = _seed_sdd_minimal(repo2)
                seeded = [
                    {"id": r.id, "type": r.type, "title": r.title} for r in records
                ]
                steps.append(f"seeded {len(records)} sdd-minimal record(s)")
        elif seed is not None:
            raise ArchledgerError("Unsupported --seed value (use 'minimal').")

        return {
            "schema": "archledger.sdd-init.v1",
            "dry_run": dry_run,
            "steps": steps,
            "policy_before": before_policy,
            "policy": policy,
            "seeded": seeded,
        }

    def _fmt(p: dict[str, object]) -> str:
        lines = ["SDD init:"]
        for s in p.get("steps", []):
            lines.append(f"  - {s}")
        pol = p.get("policy", {})
        lines.append("Effective policy:")
        for key in sorted(pol):
            lines.append(f"  {key}: {pol[key]}")
        return "\n".join(lines)

    _run_configured_command(state, "sdd init", _build, _fmt)


@sdd_policy_app.command("show")
def sdd_policy_show(ctx: typer.Context) -> None:
    """Print the effective [profiles.sdd] policy in human and JSON form."""
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo, paths
        from archledger.profiles import SDD_POLICY_FIELDS
        from archledger.sdd import sdd_options_from_config

        options = sdd_options_from_config(config, strict=False)
        policy = {
            "require_acceptance_criteria": options.require_acceptance_criteria,
            "require_implementation_refs": options.require_implementation_refs,
            "require_test_refs": options.require_test_refs,
            "require_bdd_gwt_for_behavior_records": (
                options.require_bdd_gwt_for_behavior_records
            ),
            "require_bdd_automation_for_accepted_records": (
                options.require_bdd_automation_for_accepted_records
            ),
        }
        return {
            "schema": "archledger.sdd-policy.v1",
            "sdd_enabled": "sdd" in config.profiles.profiles.enabled,
            "policy": policy,
            "fields": list(SDD_POLICY_FIELDS),
        }

    def _fmt(p: dict[str, object]) -> str:
        lines = [
            f"SDD enabled: {'yes' if p.get('sdd_enabled') else 'no'}",
            "Effective policy:",
        ]
        for key in sorted(p.get("policy", {})):
            lines.append(f"  {key}: {p['policy'][key]}")
        return "\n".join(lines)

    _run_configured_command(state, "sdd policy show", _build, _fmt)


@sdd_policy_app.command("set")
def sdd_policy_set(
    ctx: typer.Context,
    require_acceptance_criteria: Annotated[
        bool | None,
        typer.Option("--require-acceptance-criteria/--no-require-acceptance-criteria"),
    ] = None,
    require_implementation_refs: Annotated[
        bool | None,
        typer.Option("--require-implementation-refs/--no-require-implementation-refs"),
    ] = None,
    require_test_refs: Annotated[
        bool | None,
        typer.Option("--require-test-refs/--no-require-test-refs"),
    ] = None,
    require_bdd_gwt: Annotated[
        bool | None,
        typer.Option("--require-bdd-gwt/--no-require-bdd-gwt"),
    ] = None,
    require_bdd_automation: Annotated[
        bool | None,
        typer.Option("--require-bdd-automation/--no-require-bdd-automation"),
    ] = None,
) -> None:
    """Update [profiles.sdd] policy flags in .archledger.toml."""
    state = _state(ctx)
    overrides: dict[str, bool] = {}
    for flag, value in (
        ("require_acceptance_criteria", require_acceptance_criteria),
        ("require_implementation_refs", require_implementation_refs),
        ("require_test_refs", require_test_refs),
        ("require_bdd_gwt_for_behavior_records", require_bdd_gwt),
        ("require_bdd_automation_for_accepted_records", require_bdd_automation),
    ):
        if value is not None:
            overrides[flag] = value
    if not overrides:
        raise ArchledgerError(
            "Provide at least one --require-*/--no-require-* flag to set."
        )

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del repo, config
        from archledger.profiles import set_sdd_profile_policy

        before, after = set_sdd_profile_policy(
            paths.config_path,
            paths.archledger_dir,
            overrides,
        )
        changed = [k for k in overrides if before[k] != after[k]]
        return {
            "schema": "archledger.sdd-policy.v1",
            "before": before,
            "after": after,
            "changed": changed,
        }

    def _fmt(p: dict[str, object]) -> str:
        changed = p.get("changed", [])
        if not changed:
            return "No policy flags changed."
        after = p.get("after", {})
        lines = ["Updated SDD policy:"]
        for key in changed:
            lines.append(f"  {key}: {after[key]}")
        return "\n".join(lines)

    _run_configured_command(state, "sdd policy set", _build, _fmt)


@sdd_waive_app.command("add")
def sdd_waive_add(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument(help="Record to waive a rule for.")],
    rule: Annotated[
        str, typer.Option("--rule", help="SDD rule code (e.g. SDD-REQ-AC).")
    ],
    reason: Annotated[
        str,
        typer.Option("--reason", help="Non-empty waiver reason."),
    ] = "",
) -> None:
    """Add an sdd.waivers[] entry; requires a non-empty reason."""
    state = _state(ctx)
    if not reason or not reason.strip():
        raise ArchledgerError("--reason is required and must be non-empty.")

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import add_sdd_waiver
        from archledger.sdd_rules import is_known_sdd_rule

        if not is_known_sdd_rule(rule):
            raise ArchledgerError(f"Unknown SDD rule code: {rule!r}")
        target_path = _find_record_path(repo, record_id)
        _metadata, waivers = add_sdd_waiver(
            target_path,
            record_id,
            rule,
            reason,
            workspace_root=paths.workspace_root,
        )
        _validate_mutation(repo, target_path)
        return {"id": record_id, "rule": rule, "waivers": waivers}

    def _fmt(p: dict[str, object]) -> str:
        return (
            f"Waived {p.get('rule')} on {p.get('id')} "
            f"({len(p.get('waivers', []))} waiver(s))."
        )

    _run_configured_command(state, "sdd waive add", _build, _fmt)


@sdd_waive_app.command("list")
def sdd_waive_list(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument(help="Record to list waivers for.")],
) -> None:
    """List sdd.waivers[] entries for a record."""
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import list_sdd_waivers

        target_path = _find_record_path(repo, record_id)
        waivers = list_sdd_waivers(
            target_path,
            record_id,
            workspace_root=paths.workspace_root,
        )
        return {"id": record_id, "waivers": waivers}

    def _fmt(p: dict[str, object]) -> str:
        waivers = p.get("waivers", [])
        if not waivers:
            return f"No waivers on {p.get('id')}."
        lines = [f"Waivers on {p.get('id')}:"]
        for w in waivers:
            lines.append(f"  - {w.get('rule')}: {w.get('reason')}")
        return "\n".join(lines)

    _run_configured_command(state, "sdd waive list", _build, _fmt)


@sdd_waive_app.command("remove")
def sdd_waive_remove(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument(help="Record to remove a waiver from.")],
    rule: Annotated[str, typer.Option("--rule", help="SDD rule code to remove.")],
) -> None:
    """Remove the sdd.waivers[] entry matching --rule."""
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del config
        from archledger.mutations import remove_sdd_waiver

        target_path = _find_record_path(repo, record_id)
        _metadata, remaining = remove_sdd_waiver(
            target_path,
            record_id,
            rule,
            workspace_root=paths.workspace_root,
        )
        _validate_mutation(repo, target_path)
        return {"id": record_id, "rule": rule, "waivers": remaining}

    def _fmt(p: dict[str, object]) -> str:
        return (
            f"Removed waiver {p.get('rule')} on {p.get('id')} "
            f"({len(p.get('waivers', []))} remaining)."
        )

    _run_configured_command(state, "sdd waive remove", _build, _fmt)


@sdd_app.command("status")
def sdd_status(
    ctx: typer.Context,
    allow_without_profile: Annotated[
        bool,
        typer.Option(
            "--allow-without-profile",
            help=(
                "Report SDD status even when the SDD profile is not enabled "
                "(requires --reason)."
            ),
        ),
    ] = False,
    reason: Annotated[
        str | None,
        typer.Option("--reason", help="Required when using --allow-without-profile."),
    ] = None,
) -> None:
    state = _state(ctx)

    def _build_sdd_status(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths
        _enforce_sdd_profile_enabled(
            config, allow_without_profile=allow_without_profile, reason=reason
        )
        from archledger.sdd import check_sdd_status

        result = check_sdd_status(repo)
        return _sdd_status_payload(result)

    _run_configured_command(
        state, "sdd status", _build_sdd_status, _format_sdd_status_message
    )


@sdd_app.command("check")
def sdd_check(
    ctx: typer.Context,
    strict: Annotated[bool, typer.Option("--strict")] = False,
    require_acceptance_criteria: Annotated[
        bool | None,
        typer.Option(
            "--require-acceptance-criteria/--no-require-acceptance-criteria",
            help=(
                "Override config: require acceptance criteria for accepted "
                "requirements."
            ),
        ),
    ] = None,
    require_implementation_refs: Annotated[
        bool | None,
        typer.Option(
            "--require-implementation-refs/--no-require-implementation-refs",
            help=(
                "Override config: require implementation source_refs for "
                "accepted requirements."
            ),
        ),
    ] = None,
    require_test_refs: Annotated[
        bool | None,
        typer.Option(
            "--require-test-refs/--no-require-test-refs",
            help=(
                "Override config: require validation/test refs for accepted "
                "requirements."
            ),
        ),
    ] = None,
    require_bdd_gwt: Annotated[
        bool | None,
        typer.Option(
            "--require-bdd-gwt/--no-require-bdd-gwt",
            help=(
                "Override config: require Given/When/Then for accepted"
                " runtime_scenario records with bdd metadata."
            ),
        ),
    ] = None,
    require_bdd_automation: Annotated[
        bool | None,
        typer.Option(
            "--require-bdd-automation/--no-require-bdd-automation",
            help=(
                "Override config: require wired automation for accepted"
                " records with bdd metadata."
            ),
        ),
    ] = None,
    include_drafts: Annotated[
        bool,
        typer.Option("--include-drafts", help="Also evaluate draft records."),
    ] = False,
    include_superseded: Annotated[
        bool,
        typer.Option("--include-superseded", help="Also evaluate superseded records."),
    ] = False,
    all_statuses: Annotated[
        bool,
        typer.Option("--all-statuses", help="Evaluate records of every status."),
    ] = False,
    allow_without_profile: Annotated[
        bool,
        typer.Option(
            "--allow-without-profile",
            help=(
                "Lint ad hoc even when the SDD profile is not enabled "
                "(requires --reason)."
            ),
        ),
    ] = False,
    reason: Annotated[
        str | None,
        typer.Option("--reason", help="Required when using --allow-without-profile."),
    ] = None,
    scope_record: Annotated[
        str | None,
        typer.Option(
            "--record",
            help="Scope findings to a specific record id.",
        ),
    ] = None,
    scope_kind: Annotated[
        str | None,
        typer.Option(
            "--kind",
            help="Scope findings to records of a given type (e.g. requirement, adr).",
        ),
    ] = None,
) -> None:
    state = _state(ctx)

    def _build_sdd_check(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths
        _enforce_sdd_profile_enabled(
            config, allow_without_profile=allow_without_profile, reason=reason
        )
        from archledger.sdd import check_sdd, sdd_options_from_config

        options = sdd_options_from_config(
            config,
            strict=strict,
            require_acceptance_criteria=require_acceptance_criteria,
            require_implementation_refs=require_implementation_refs,
            require_test_refs=require_test_refs,
            require_bdd_gwt_for_behavior_records=require_bdd_gwt,
            require_bdd_automation_for_accepted_records=require_bdd_automation,
            include_draft=include_drafts or all_statuses,
            include_superseded=include_superseded or all_statuses,
        )
        result = check_sdd(repo, options=options)
        if scope_record or scope_kind:
            from archledger.model import normalize_kind
            from archledger.sdd import SddCheckResult

            allowed_ids: set[str] = set()
            if scope_record:
                allowed_ids.add(scope_record)
            if scope_kind:
                norm_kind = normalize_kind(scope_kind.replace("-", "_"))
                allowed_ids.update(
                    r.id for r in repo.load_all_records() if r.type == norm_kind
                )
            result = SddCheckResult(
                errors=tuple(f for f in result.errors if f.record_id in allowed_ids),
                warnings=tuple(
                    f for f in result.warnings if f.record_id in allowed_ids
                ),
                summary=result.summary,
            )
        if result.has_failures(strict=strict):
            raise ArchledgerError(
                f"SDD check failed with {len(result.errors)} error(s) "
                f"and {len(result.warnings)} warning(s).",
                details=_sdd_check_payload(result, config, options=options),
            )
        return _sdd_check_payload(result, config, options=options)

    _run_configured_command(
        state, "sdd check", _build_sdd_check, _format_sdd_check_message
    )


@sdd_app.command("check-pr")
def sdd_check_pr(
    ctx: typer.Context,
    against: Annotated[str, typer.Option("--against")],
    strict: Annotated[bool, typer.Option("--strict")] = False,
    allow_without_profile: Annotated[
        bool,
        typer.Option(
            "--allow-without-profile",
            help=(
                "Run the PR gate even when the SDD profile is not enabled "
                "(requires --reason)."
            ),
        ),
    ] = False,
    reason: Annotated[
        str | None,
        typer.Option("--reason", help="Required when using --allow-without-profile."),
    ] = None,
    allow_unlinked: Annotated[
        bool,
        typer.Option(
            "--allow-unlinked",
            help="Do not fail when changed files have no referencing record.",
        ),
    ] = False,
) -> None:
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        from archledger.sdd import check_sdd, sdd_options_from_config
        from archledger.source_tracking import scan_git_revision

        _enforce_sdd_profile_enabled(
            config, allow_without_profile=allow_without_profile, reason=reason
        )

        baseline = scan_git_revision(
            paths,
            config,
            against,
            reason=f"git:{against}",
        )
        current = scan_workspace(paths, config, reason="sdd-check-pr")
        changes = resolve_impacts(
            repo.load_all_records(include_sections=True),
            diff_source_states(baseline, current),
            include_draft=True,
            include_superseded=False,
        )
        options = sdd_options_from_config(config, strict=strict)
        result = check_sdd(repo, options=options)
        payload = {
            "schema": "archledger.sdd-pr.v1",
            "against": against,
            "changes": _changed_payload(paths, changes),
            "sdd": _sdd_check_payload(result, config, options=options),
        }
        unlinked = list(changes.unlinked_changed_files)
        if unlinked and not allow_unlinked:
            raise ArchledgerError(
                f"SDD PR check failed: {len(unlinked)} unlinked changed file(s).",
                details=payload,
            )
        if result.has_failures(strict=strict):
            raise ArchledgerError(
                "SDD PR check failed.",
                details=payload,
            )
        return payload

    _run_configured_command(
        state,
        "sdd check-pr",
        _build,
        lambda payload: (
            f"SDD PR check against {payload.get('against')}: "
            f"{len(payload.get('changes', {}).get('changed_files', []))} changed."
            if isinstance(payload.get("changes"), dict)
            else "SDD PR check complete."
        ),
    )


@sdd_app.command("explain")
def sdd_explain(
    ctx: typer.Context,
    code: Annotated[
        str | None,
        typer.Argument(help="SDD rule code to explain (e.g. SDD-REQ-AC)."),
    ] = None,
    all_rules: Annotated[
        bool,
        typer.Option("--all", help="Explain every registered SDD rule."),
    ] = False,
) -> None:
    """Explain one or all SDD rule codes (severity, meaning, fix, waiver)."""
    from archledger.cli_payloads import sdd_explain_all_payload, sdd_explain_payload
    from archledger.sdd_rules import (
        all_sdd_rules,
        get_sdd_rule,
        known_sdd_rule_codes,
    )

    state = _state(ctx)

    def _build() -> dict[str, object]:
        if not code and not all_rules:
            raise ArchledgerError(
                "Provide an SDD rule code or pass --all.",
                details={"known_codes": list(known_sdd_rule_codes())},
            )
        if all_rules:
            return sdd_explain_all_payload(all_sdd_rules())
        info = get_sdd_rule(code or "")
        if info is None:
            raise ArchledgerError(
                f"Unknown SDD rule code: {code!r}",
                details={"known_codes": list(known_sdd_rule_codes())},
            )
        return sdd_explain_payload(info)

    try:
        payload = _build()
    except ArchledgerError as exc:
        _emit_error(state, "sdd explain", exc)
        return

    if all_rules:

        def _fmt(p: dict[str, object]) -> str:
            lines = [f"SDD rules ({len(p.get('rules', []))}):"]
            for r in p.get("rules", []):
                lines.append(
                    f"  {r.get('code')} [{r.get('severity')}] {r.get('meaning')}"
                )
            return "\n".join(lines)
    else:

        def _fmt(p: dict[str, object]) -> str:
            lines = [
                f"{p.get('code')}",
                f"Severity: {p.get('severity')}",
                f"Meaning: {p.get('meaning')}",
                f"Fix: {p.get('fix')}",
                f"Waivable: {'yes' if p.get('waivable') else 'no'}",
            ]
            if p.get("waiver_example"):
                lines.append("Waiver front matter:")
                lines.append(str(p.get("waiver_example")))
            return "\n".join(lines)

    _emit_success(
        state,
        command="sdd explain",
        result=payload,
        warnings=[],
        human_message=_fmt(payload),
    )


@sdd_app.command("coverage")
def sdd_coverage(
    ctx: typer.Context,
    by_record: Annotated[
        bool,
        typer.Option("--by-record", help="Per-record detail (JSON only)."),
    ] = False,
    include_bdd: Annotated[
        bool,
        typer.Option("--include-bdd", help="Include BDD coverage dimensions."),
    ] = False,
    format: Annotated[
        str,
        typer.Option("--format", help="Output format: human, markdown."),
    ] = "human",
) -> None:
    """Detailed SDD coverage report with gaps and optional BDD dimensions."""
    state = _state(ctx)

    def _build(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        from archledger.sdd import check_sdd_coverage

        result = check_sdd_coverage(repo, include_bdd=include_bdd, by_record=by_record)
        dim_payload = {
            k: {"covered": d.covered, "total": d.total}
            for k, d in result.coverage.items()
        }
        return {
            "schema": "archledger.sdd-coverage.v1",
            "sdd_enabled": result.sdd_enabled,
            "totals": result.totals,
            "coverage": dim_payload,
            "gaps": list(result.gaps),
        }

    def _fmt(p: dict[str, object]) -> str:
        totals = p.get("totals", {})
        cov = p.get("coverage", {})
        gaps = p.get("gaps", [])
        lines = ["SDD coverage:"]
        lines.append(
            f"  Accepted requirements: {totals.get('accepted_requirements', 0)}"
        )
        for key in sorted(cov):
            d = cov[key]
            lines.append(f"  {key}: {d['covered']}/{d['total']}")
        if gaps:
            lines.append("Gaps:")
            for g in gaps:
                lines.append(f"  - {g}")
        return "\n".join(lines)

    _run_configured_command(state, "sdd coverage", _build, _fmt)


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


def _seed_sdd_minimal(repo: ArchitectureRepository) -> list[ArchitectureRecord]:
    req = repo.create_record("requirement", "Example requirement", status="draft")
    ac = repo.create_record(
        "acceptance-criterion",
        "Example requirement is validated",
        status="draft",
        requirement=req.id,
    )
    created_records: list[ArchitectureRecord] = [
        req,
        ac,
        repo.create_record(
            "quality-scenario",
            "Agent context remains bounded",
            status="draft",
        ),
        repo.create_record(
            "adr",
            "Use archledger as the SDD contract",
            status="draft",
        ),
        repo.create_record(
            "risk",
            "Specification drift between source and records",
            status="draft",
        ),
        repo.create_record(
            "glossary-term",
            "Acceptance criterion",
            status="draft",
        ),
    ]
    return created_records
