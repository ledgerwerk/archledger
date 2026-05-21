from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Annotated

import typer

from archledger import __version__
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
    format_init_message as _format_init_message,
)
from archledger.cli_formatting import (
    format_list_message as _format_list_message,
)
from archledger.cli_formatting import (
    format_new_message as _format_new_message,
)
from archledger.cli_formatting import (
    format_read_message as _format_read_message,
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
from archledger.cli_formatting import (
    format_where_message as _format_where_message,
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
from archledger.migration import convert_sources
from archledger.model import ArchitectureRecord
from archledger.render import build_document
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
    render_default_config,
)
from archledger.storage.source_state import read_source_state, write_source_state

app = typer.Typer(add_completion=False, no_args_is_help=True)


@dataclass(frozen=True, slots=True)
class CLIState:
    root: Path
    json_output: bool


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
    source_format: Annotated[
        str,
        typer.Option(
            "--source-format",
            help="Canonical source dialect for new project fragments.",
        ),
    ] = "asciidoc",
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
        config_text = render_default_config(
            workspace_root,
            archledger_dir=archledger_dir,
            source_format=source_format,
            project_name=project_name,
        )
        write_text_atomic(config_path, config_text)
        paths, config, warnings = resolve_project_paths(workspace_root)
        repo = ArchitectureRepository(paths, config)
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


@app.command()
def where(ctx: typer.Context) -> None:
    state = _state(ctx)
    _run_configured_command(
        state,
        "where",
        _where_payload,
        _format_where_message,
    )


@app.command("new")
def new_record(
    ctx: typer.Context,
    kind: Annotated[str, typer.Argument()],
    title: Annotated[
        str,
        typer.Option("--title", help="Human-readable record title."),
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
    include_draft: Annotated[bool, typer.Option("--include-draft")] = False,
) -> None:
    state = _state(ctx)

    def build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        return _list_payload(repo.list_records(include_draft=include_draft, kind=kind))

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
    include_body: Annotated[bool, typer.Option("--include-body")] = False,
    include_draft: Annotated[bool, typer.Option("--include-draft")] = False,
    include_superseded: Annotated[bool, typer.Option("--include-superseded")] = False,
    section: Annotated[str | None, typer.Option("--section")] = None,
    kind: Annotated[str | None, typer.Option("--kind")] = None,
) -> None:
    state = _state(ctx)

    def build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        return _read_payload(
            repo,
            paths,
            config,
            include_body=include_body,
            include_draft=include_draft,
            include_superseded=include_superseded,
            section=section,
            kind=kind,
        )

    _run_configured_command(state, "read", build_result, _format_read_message)


@app.command()
def check(
    ctx: typer.Context,
    strict: Annotated[bool, typer.Option("--strict")] = False,
    repair_counters: Annotated[bool, typer.Option("--repair-counters")] = False,
) -> None:
    state = _state(ctx)

    def build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        result = repo.check(strict=strict, repair_counters=repair_counters)
        if result.has_failures(strict=strict):
            raise _check_error(result, strict=strict)
        return _check_payload(result)

    _run_configured_command(state, "check", build_result, _format_check_message)


@app.command()
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

    _run_configured_command(state, "snapshot", build_result, _format_snapshot_message)


@app.command()
def changed(
    ctx: typer.Context,
    include_draft: Annotated[bool, typer.Option("--include-draft")] = False,
    include_superseded: Annotated[bool, typer.Option("--include-superseded")] = False,
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
        baseline = _load_tracking_baseline(paths, config)
        current = scan_workspace(paths, config, reason="current-scan")
        changes = diff_source_states(baseline, current)
        if baseline is not None:
            changes = resolve_impacts(
                repo.load_all_records(include_sections=True),
                changes,
                include_draft=include_draft,
                include_superseded=include_superseded,
            )
        return _changed_payload(paths, changes)

    _run_configured_command(state, "changed", build_result, _format_changed_message)


@app.command()
def build(
    ctx: typer.Context,
    output: Annotated[Path | None, typer.Option("--output")] = None,
    format: Annotated[str | None, typer.Option("--format")] = None,
    formats: Annotated[str | None, typer.Option("--formats")] = None,
    all_formats: Annotated[bool, typer.Option("--all")] = False,
    include_draft: Annotated[bool, typer.Option("--include-draft")] = False,
    include_superseded: Annotated[bool, typer.Option("--include-superseded")] = False,
    strict: Annotated[bool, typer.Option("--strict")] = False,
) -> None:
    state = _state(ctx)

    def build_result(
        repo: ArchitectureRepository,
        paths: ProjectPaths,
        config: ProjectConfig,
    ) -> dict[str, object]:
        del paths, config
        result = build_document(
            repo,
            output=output,
            format=format,
            formats=formats,
            all_formats=all_formats,
            include_draft=include_draft,
            include_superseded=include_superseded,
            strict=strict,
        )
        return _build_payload(result)

    _run_configured_command(state, "build", build_result, _format_build_message)


@app.command("convert-sources")
def convert_sources_command(
    ctx: typer.Context,
    to: Annotated[str, typer.Option("--to")] = "asciidoc",
    write: Annotated[bool, typer.Option("--write")] = False,
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
            write=write,
            replace=replace,
            allow_mixed_body_format=allow_mixed_body_format,
        )
        return _convert_sources_payload(result)

    _run_configured_command(
        state,
        "convert-sources",
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
        typer.echo(
            json.dumps(
                {
                    "ok": True,
                    "command": command,
                    "result": result,
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
