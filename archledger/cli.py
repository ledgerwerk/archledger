from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
import yaml

from archledger import __version__
from archledger.errors import ArchledgerError
from archledger.migration import convert_sources
from archledger.model import ArchitectureRecord
from archledger.render import build_document
from archledger.repository import (
    ArchitectureRepository,
    CheckFinding,
    CheckResult,
    InitResult,
    StatusResult,
)
from archledger.storage.common import write_text
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
            project_name=project_name,
        )
        write_text(config_path, config_text)
        paths, config, warnings = resolve_project_paths(workspace_root)
        repo = ArchitectureRepository(paths, config)
        result = repo.init()
        _emit_success(
            state,
            command="init",
            result={
                "workspace_root": str(result.workspace_root),
                "config_path": str(result.config_path),
                "archledger_dir": str(result.archledger_dir),
                "created_paths": [str(path) for path in result.created_paths],
            },
            warnings=warnings,
            human_message=_format_init_message(result),
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
        record = repo.create_record(
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
        return {
            "id": record.id,
            "type": record.type,
            "path": str(record.path),
        }

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
        return {
            "preset": preset,
            "records": [
                {
                    "id": record.id,
                    "type": record.type,
                    "path": str(record.path),
                }
                for record in records
            ],
        }

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
        records = repo.list_records(include_draft=include_draft, kind=kind)
        return {
            "records": [
                {
                    "id": record.id,
                    "type": record.type,
                    "status": record.status,
                    "section": record.section,
                    "title": record.title,
                    "path": str(record.path),
                }
                for record in records
            ]
        }

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
        record = repo.get_record(record_id)
        return {
            "id": record.id,
            "type": record.type,
            "status": record.status,
            "section": record.section,
            "title": record.title,
            "path": str(record.path),
            "metadata": record.metadata,
            "body": record.body,
        }

    _run_configured_command(state, "show", build_result, _format_show_message)


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
        return {
            "assembled_path": str(result.assembled_path),
            "outputs": [
                {
                    "format": output_result.format,
                    "output_path": str(output_result.output_path),
                }
                for output_result in result.outputs
            ],
        }

    _run_configured_command(state, "build", build_result, _format_build_message)


@app.command("convert-sources")
def convert_sources_command(
    ctx: typer.Context,
    to: Annotated[str, typer.Option("--to")] = "asciidoc",
    write: Annotated[bool, typer.Option("--write")] = False,
    replace: Annotated[bool, typer.Option("--replace")] = False,
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
        )
        return {
            "target_format": result.target_format,
            "write": result.write,
            "replace": result.replace,
            "config_path": str(result.config_path),
            "converted": [
                {
                    "source_path": str(item.source_path),
                    "output_path": str(item.output_path),
                    "body_format": item.body_format,
                }
                for item in result.converted
            ],
            "warnings": list(result.warnings),
        }

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


def _status_payload(
    repo: ArchitectureRepository,
    paths: ProjectPaths,
    config: ProjectConfig,
) -> dict[str, object]:
    status_result: StatusResult = repo.status()
    return {
        "workspace_root": str(status_result.workspace_root),
        "config_path": str(status_result.config_path),
        "archledger_dir": str(status_result.archledger_dir),
        "storage_meta_path": str(status_result.storage_meta_path),
        "build_dir": str(status_result.build_dir),
        "sections_count": status_result.sections_count,
        "record_directories_count": status_result.record_directories_count,
        "project_name": config.project_name,
        "project_uuid": config.project_uuid,
    }


def _where_payload(
    repo: ArchitectureRepository,
    paths: ProjectPaths,
    config: ProjectConfig,
) -> dict[str, object]:
    del repo, config
    return {
        "workspace_root": str(paths.workspace_root),
        "config_path": str(paths.config_path),
        "archledger_dir": str(paths.archledger_dir),
        "sections_dir": str(paths.sections_dir),
        "records_dir": str(paths.records_dir),
        "build_dir": str(paths.build_dir),
        "storage_meta_path": str(paths.storage_meta_path),
    }


def _format_init_message(result: InitResult) -> str:
    return "\n".join(
        [
            f"Initialized archledger in {result.workspace_root}",
            f"Config: {result.config_path}",
            f"State: {result.archledger_dir}",
        ]
    )


def _format_status_message(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            f"Project: {payload['project_name']}",
            f"Workspace: {payload['workspace_root']}",
            f"Config: {payload['config_path']}",
            f"State: {payload['archledger_dir']}",
            f"Sections: {payload['sections_count']}",
            f"Record directories: {payload['record_directories_count']}",
        ]
    )


def _format_where_message(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            f"Workspace: {payload['workspace_root']}",
            f"Config: {payload['config_path']}",
            f"State: {payload['archledger_dir']}",
            f"Sections: {payload['sections_dir']}",
            f"Records: {payload['records_dir']}",
            f"Build: {payload['build_dir']}",
            f"Storage metadata: {payload['storage_meta_path']}",
        ]
    )


def _format_new_message(payload: dict[str, object]) -> str:
    return f"Created {payload['id']}: {payload['path']}"


def _format_seed_message(payload: dict[str, object]) -> str:
    records = payload.get("records")
    if not isinstance(records, list):
        raise RuntimeError("Seed payload was malformed.")
    return (
        f"Seeded {payload['preset']} with {len(records)} record(s)."
    )


def _format_list_message(payload: dict[str, object]) -> str:
    records = payload["records"]
    if not isinstance(records, list) or not records:
        return "No records found."
    lines = []
    for item in records:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"{item['id']}  {item['type']}  {item['status']}  {item['title']}"
        )
    return "\n".join(lines)


def _format_show_message(payload: dict[str, object]) -> str:
    metadata = payload["metadata"]
    body = payload["body"]
    if not isinstance(metadata, dict) or not isinstance(body, str):
        raise RuntimeError("Show payload was malformed.")
    yaml_text = yaml.safe_dump(metadata, sort_keys=False).rstrip()
    document = f"Path: {payload['path']}\n---\n{yaml_text}\n---"
    if body:
        document = f"{document}\n\n{body.rstrip()}"
    return document


def _format_check_message(payload: dict[str, object]) -> str:
    error_messages = payload["errors"]
    warning_messages = payload["warnings"]
    if not isinstance(error_messages, list) or not isinstance(warning_messages, list):
        raise RuntimeError("Check payload was malformed.")
    lines = [
        (
            "Check completed: "
            f"{len(error_messages)} error(s), "
            f"{len(warning_messages)} warning(s)"
        ),
    ]
    for entry in error_messages:
        if isinstance(entry, dict):
            lines.append(f"error: {entry['message']}")
    for entry in warning_messages:
        if isinstance(entry, dict):
            lines.append(f"warning: {entry['message']}")
    if payload.get("repaired_counters"):
        lines.append("Counters repaired.")
    return "\n".join(lines)


def _format_build_message(payload: dict[str, object]) -> str:
    outputs = payload.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise RuntimeError("Build payload was malformed.")
    if len(outputs) == 1 and isinstance(outputs[0], dict):
        return f"Built {outputs[0]['format']}: {outputs[0]['output_path']}"

    lines = ["Built outputs:"]
    for item in outputs:
        if isinstance(item, dict):
            lines.append(f"{item['format']}: {item['output_path']}")
    return "\n".join(lines)


def _format_convert_sources_message(payload: dict[str, object]) -> str:
    converted = payload.get("converted")
    warnings = payload.get("warnings")
    if not isinstance(converted, list) or not isinstance(warnings, list):
        raise RuntimeError("convert-sources payload was malformed.")
    action = "Converted" if payload.get("write") else "Planned"
    lines = [
        f"{action} {len(converted)} source file(s) to {payload['target_format']}.",
    ]
    if not payload.get("write"):
        lines.append("Re-run with --write to apply the migration.")
    for warning in warnings:
        lines.append(f"warning: {warning}")
    return "\n".join(lines)


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


def _check_payload(result: CheckResult) -> dict[str, object]:
    return {
        "errors": [_finding_payload(finding) for finding in result.errors],
        "warnings": [_finding_payload(finding) for finding in result.warnings],
        "repaired_counters": result.repaired_counters,
    }


def _finding_payload(finding: CheckFinding) -> dict[str, object]:
    payload: dict[str, object] = {"level": finding.level, "message": finding.message}
    if finding.path is not None:
        payload["path"] = str(finding.path)
    return payload


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
