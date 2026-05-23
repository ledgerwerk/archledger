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
    ] = "asciidoc",
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
) -> None:
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
        config = build_default_project_config(
            workspace_root,
            archledger_dir=archledger_dir,
            source_format=source_format,
            id_prefix=id_prefix,
            id_width=id_width,
            id_segment_mode=id_segment_mode,
            project_name=project_name,
            project_uuid=project_uuid,
            build_default_format=build_default_format,
            build_default_output=build_default_output,
            build_default_output_dir=build_default_output_dir,
            build_include_draft=build_include_draft,
            build_include_superseded=build_include_superseded,
            build_strict=build_strict,
            build_keep_intermediate=build_keep_intermediate,
            build_converter=build_converter,
            build_pdf_engine=build_pdf_engine,
            build_reference_docx=build_reference_docx,
            diagram_enabled=diagrams,
            diagram_renderer=diagram_renderer,
            diagram_default_type=diagram_default_type,
            diagram_output_dir=diagram_output_dir,
            diagram_image_format=diagram_image_format,
            diagram_kroki_url=diagram_kroki_url,
            arc42_title=arc42_title,
            arc42_language=arc42_language,
            arc42_template_version=arc42_template_version,
            arc42_include_help=arc42_include_help,
            tracking_enabled=tracking,
            tracking_scanner=tracking_scanner,
            tracking_state_file=tracking_state_file,
            tracking_max_file_bytes=tracking_max_file_bytes,
            tracking_include=tuple(tracking_include) if tracking_include else None,
            tracking_exclude=tuple(tracking_exclude) if tracking_exclude else None,
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
    state = _state(ctx)
    _run_configured_command(
        state,
        "status",
        _status_payload,
        _format_status_message,
    )


@app.command("paths")
def paths(ctx: typer.Context) -> None:
    state = _state(ctx)
    _run_configured_command(
        state,
        "paths",
        _where_payload,
        _format_paths_message,
    )


@app.command("schema")
def schema(ctx: typer.Context) -> None:
    state = _state(ctx)
    _run_configured_command(
        state,
        "schema",
        _schema_payload,
        _format_schema_message,
    )


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
) -> None:
    state = _state(ctx)

    def build_result(
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
            )
        )

    _run_configured_command(state, "new", build_result, _format_new_message)


@app.command()
def seed(
    ctx: typer.Context,
    preset: Annotated[str, typer.Argument()],
) -> None:
    state = _state(ctx)

    def build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        if preset != "arc42-minimal":
            raise ArchledgerError(f"Unsupported seed preset: {preset}")
        records = _seed_arc42_minimal(repo)
        return _seed_payload(preset, records)

    _run_configured_command(state, "seed", build_result, _format_seed_message)


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

    def build_result(
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

    _run_configured_command(state, "list", build_result, _format_list_message)


@app.command()
def show(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument()],
) -> None:
    state = _state(ctx)

    def build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        return _show_payload(repo.get_record(record_id))

    _run_configured_command(state, "show", build_result, _format_show_message)


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

    def build_result(
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

    _run_configured_command(state, "read", build_result, _format_read_message)


@app.command()
def check(
    ctx: typer.Context,
    strict: Annotated[bool, typer.Option("--strict")] = False,
) -> None:
    state = _state(ctx)

    def build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        result = repo.check(strict=strict)
        if result.has_failures(strict=strict):
            raise _check_error(result, strict=strict)
        return _check_payload(result)

    _run_configured_command(state, "check", build_result, _format_check_message)


@app.command("archive")
def archive(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument(help="Ledger ID to archive.")],
    reason: Annotated[str, typer.Option("--reason", help="Archive reason.")] = "",
) -> None:
    state = _state(ctx)

    def build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        return _archive_payload(repo.archive_record(record_id, reason=reason))

    _run_configured_command(state, "archive", build_result, _format_archive_message)


@app.command("doctor")
def doctor(
    ctx: typer.Context,
    repair: Annotated[bool, typer.Option("--repair")] = False,
) -> None:
    state = _state(ctx)

    def build_result(
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

    _run_configured_command(state, "doctor", build_result, _format_doctor_message)


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

    def build_result(
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
        build_result,
        _format_renumber_message,
    )


@source_app.command("snapshot")
def snapshot(
    ctx: typer.Context,
    reason: Annotated[str, typer.Option("--reason")] = "manual",
) -> None:
    state = _state(ctx)

    def build_result(
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
        build_result,
        _format_snapshot_message,
    )


@source_app.command("changed")
def changed(
    ctx: typer.Context,
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

    def build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        repo.status()
        if not config.tracking_enabled:
            raise StorageError(
                "Source tracking is disabled by [tracking].enabled = false."
            )
        baseline = _load_tracking_baseline(paths, config)
        current = scan_workspace(paths, config, reason="current-scan")
        changes = diff_source_states(baseline, current)
        if baseline is not None:
            changes = resolve_impacts(
                repo.load_all_records(include_sections=True),
                changes,
                include_draft=visibility.include_drafts,
                include_superseded=visibility.include_superseded,
            )
        return _changed_payload(paths, changes)

    _run_configured_command(
        state,
        "source changed",
        build_result,
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

    def build_result(
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

    _run_configured_command(state, "build", build_result, _format_build_message)


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

    def build_result(
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
        build_result,
        _format_convert_sources_message,
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
