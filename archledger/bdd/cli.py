"""``archledger bdd`` sub-app.

Contains the ``import`` command for creating archledger records from Gherkin
feature files.  The actual parsing and record creation lives in
``archledger.bdd.gherkin`` and ``archledger.bdd.importer``; this module
handles only CLI option parsing, JSON payload emission, and human-readable
output formatting.
"""

from __future__ import annotations

from typing import Annotated

import typer

from archledger.bdd.gherkin import (
    GherkinSyntaxError,
    UnsupportedGherkinError,
)
from archledger.errors import ArchledgerError

bdd_app = typer.Typer(add_completion=False, no_args_is_help=True)


def _gherkin_construct(message: str) -> str:
    """Best-effort extract of the unsupported construct keyword from a message."""
    for keyword in (
        "Background:",
        "Scenario Outline:",
        "Scenario Template:",
        "Examples:",
        "Scenarios:",
    ):
        if keyword in message:
            return keyword
    return ""


def _translate_gherkin_error(
    exc: Exception,
    *,
    feature_file: str,
) -> ArchledgerError:
    """Convert a Gherkin parser error into a structured ArchledgerError.

    Preserves ``line``, ``construct``, and ``feature_file`` so JSON consumers
    can locate the problem without re-parsing the message text.
    """
    if isinstance(exc, (UnsupportedGherkinError, GherkinSyntaxError)):
        return ArchledgerError(
            str(exc),
            details={
                "type": exc.__class__.__name__,
                "message": str(exc),
                "line": getattr(exc, "line", 0),
                "construct": _gherkin_construct(str(exc)),
                "feature_file": feature_file,
            },
        )
    return ArchledgerError(str(exc))


def _import_result_format_human(payload: dict[str, object]) -> str:
    """Human-readable summary for ``bdd import``."""
    records = payload.get("created_records", [])
    feature_file = payload.get("feature_file", "")
    lines = [f"Imported {len(records)} scenario(s) from {feature_file}:"]
    for rec in records:
        lines.append(f"  - {rec['id']} ({rec['type']}): {rec['title']}")
    warnings = payload.get("warnings", [])
    for warning in warnings:
        lines.append(f"  warning: {warning}")
    return "\n".join(lines)


@bdd_app.command("import")
def import_command(
    ctx: typer.Context,
    feature_file: Annotated[
        str,
        typer.Argument(help="Path to the .feature file (relative to workspace root)."),
    ],
    kind: Annotated[
        str,
        typer.Option(
            "--kind",
            help="Record kind: runtime-scenario or quality-scenario.",
        ),
    ] = "runtime-scenario",
    status: Annotated[
        str,
        typer.Option("--status", help="Initial record status."),
    ] = "proposed",
    section: Annotated[
        str | None,
        typer.Option(
            "--section",
            help="Override the default target section.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Parse and preview without creating records."),
    ] = False,
) -> None:
    """Import a Gherkin feature file into archledger as behavior records."""
    from archledger.bdd.importer import BddImportResponse, import_bdd_feature
    from archledger.cli import _run_configured_command, _state
    from archledger.cli_payloads import bdd_import_payload

    state = _state(ctx)

    def _build_import_result(repo, paths, config):  # noqa: ANN001
        del paths, config
        try:
            if dry_run:
                from pathlib import Path

                from archledger.bdd.gherkin import parse_gherkin
                from archledger.source_refs import validate_relative_posix_path

                safe_path = validate_relative_posix_path(
                    feature_file, field_name="Feature file"
                )
                absolute_path = repo.paths.workspace_root / Path(safe_path)
                if not absolute_path.is_file():
                    raise FileNotFoundError(f"Feature file does not exist: {safe_path}")
                text = absolute_path.read_text(encoding="utf-8")
                feature = parse_gherkin(text)
                preview = [
                    {
                        "name": s.name,
                        "rule": s.rule,
                        "tags": list(s.tags),
                        "given": list(s.given),
                        "when": list(s.when),
                        "then": list(s.then),
                    }
                    for s in feature.scenarios
                ]
                return {
                    "schema": "archledger.bdd-import.v1",
                    "feature_file": safe_path,
                    "dry_run": True,
                    "scenarios_preview": preview,
                    "created_records": [],
                    "warnings": [],
                }
            response: BddImportResponse = import_bdd_feature(
                repo,
                feature_file,
                kind=kind,
                status=status,
                section=section,
            )
        except UnsupportedGherkinError as exc:
            raise _translate_gherkin_error(exc, feature_file=feature_file) from exc
        except GherkinSyntaxError as exc:
            raise _translate_gherkin_error(exc, feature_file=feature_file) from exc
        except (ValueError, FileNotFoundError, ArchledgerError) as exc:
            raise ArchledgerError(str(exc)) from exc
        return bdd_import_payload(response)

    _run_configured_command(
        state,
        "bdd import",
        _build_import_result,
        _import_result_format_human,
    )


@bdd_app.command("export")
def export_command(
    ctx: typer.Context,
    record_id: Annotated[
        str | None,
        typer.Argument(
            help="Archledger record ID to export (omit with --all or --feature)."
        ),
    ] = None,
    out: Annotated[
        str | None,
        typer.Option(
            "--out",
            help=("Output .feature file path (single record or --feature mode)."),
        ),
    ] = None,
    out_dir: Annotated[
        str | None,
        typer.Option(
            "--out-dir",
            help="Output directory for --all mode (created if needed).",
        ),
    ] = None,
    feature: Annotated[
        str | None,
        typer.Option("--feature", help="Export all scenarios for this feature name."),
    ] = None,
    all_records: Annotated[
        bool,
        typer.Option("--all", help="Export all records with bdd metadata."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing output files."),
    ] = False,
) -> None:
    """Export archledger record(s) with bdd metadata as Gherkin feature files."""
    from archledger.bdd.exporter import export_bdd_record, render_feature_from_example
    from archledger.bdd.inspect import list_bdd_records
    from archledger.bdd.normalize import normalize_bdd_metadata
    from archledger.cli import _run_configured_command, _state
    from archledger.cli_payloads import bdd_export_payload
    from archledger.source_refs import validate_relative_posix_path

    state = _state(ctx)

    # Validate option combinations.
    modes = sum(bool(x) for x in (record_id, all_records, feature))
    if modes == 0:
        raise ArchledgerError("Provide a RECORD_ID, --all, or --feature.")
    if modes > 1:
        raise ArchledgerError("Use only one of RECORD_ID, --all, or --feature.")
    if (all_records or feature) and not out_dir:
        raise ArchledgerError("--all and --feature require --out-dir.")
    if record_id and not out:
        raise ArchledgerError("Single-record export requires --out.")

    def _build_export_result(repo, paths, config):  # noqa: ANN001
        del config
        try:
            # Single-record mode
            if record_id and out:
                response = export_bdd_record(repo, record_id, out, force=force)
                return bdd_export_payload(response)

            # Batch mode (--all or --feature)
            from pathlib import Path

            entries = list_bdd_records(
                repo, feature_filter=feature if not all_records else None
            )
            if not entries.entries:
                return {
                    "schema": "archledger.bdd-export.v1",
                    "exported": [],
                    "feature_files": [],
                }

            exported: list[dict[str, object]] = []
            feature_files: list[str] = []
            safe_dir = validate_relative_posix_path(
                out_dir or ".", field_name="out-dir"
            )
            out_path = paths.workspace_root / Path(safe_dir)
            out_path.mkdir(parents=True, exist_ok=True)

            # Group by feature+rule for deterministic multi-scenario files
            groups: dict[tuple[str, str], list[str]] = {}
            for entry in entries.entries:
                groups.setdefault((entry.feature, entry.rule), []).append(
                    entry.record_id
                )

            for (feat, rule), rids in sorted(groups.items()):
                scenario_parts = []
                for rid in rids:
                    record = repo.get_record(rid)
                    raw_bdd = record.metadata.get("bdd")
                    if raw_bdd is None:
                        continue
                    example, _ = normalize_bdd_metadata(rid, raw_bdd)
                    if example is None:
                        continue
                    scenario_parts.append(example)
                if not scenario_parts:
                    continue
                content = render_feature_from_example(feat, rule, scenario_parts, rids)
                feat_filename = feat.lower().replace(" ", "_") + ".feature"
                file_path = out_path / feat_filename
                if file_path.exists() and not force:
                    raise ValueError(
                        f"Feature file already exists: {safe_dir}/{feat_filename}"
                        " (use --force)"
                    )
                file_path.write_text(content, encoding="utf-8")
                rel = str(file_path.relative_to(paths.workspace_root))
                feature_files.append(rel)
                exported.extend(
                    {"record_id": rid, "feature": feat, "file": rel} for rid in rids
                )

            return {
                "schema": "archledger.bdd-export.v1",
                "exported": exported,
                "feature_files": feature_files,
            }
        except UnsupportedGherkinError as exc:
            raise _translate_gherkin_error(
                exc, feature_file=out or out_dir or ""
            ) from exc
        except GherkinSyntaxError as exc:
            raise _translate_gherkin_error(
                exc, feature_file=out or out_dir or ""
            ) from exc
        except (ValueError, FileNotFoundError, ArchledgerError) as exc:
            raise ArchledgerError(str(exc)) from exc

    def _fmt_export(p: dict[str, object]) -> str:
        if p.get("record_id"):
            return (
                f"Exported {p['record_id']} to "
                f"{p.get('output_file', p.get('file', ''))}"
            )
        exported = p.get("exported", [])
        feature_files = p.get("feature_files", [])
        return (
            f"Exported {len(exported)} scenario(s) into "
            f"{len(feature_files)} feature file(s)."
        )

    _run_configured_command(
        state,
        "bdd export",
        _build_export_result,
        _fmt_export,
    )


@bdd_app.command("validate")
def validate_command(
    ctx: typer.Context,
    record_id: Annotated[
        str | None,
        typer.Argument(help="Record id to validate."),
    ] = None,
    feature_file: Annotated[
        str | None,
        typer.Option(
            "--feature-file",
            help="Validate this Gherkin file (parse-only, no import).",
        ),
    ] = None,
    all_records: Annotated[
        bool,
        typer.Option("--all", help="Validate bdd metadata on all records."),
    ] = False,
) -> None:
    """Validate BDD metadata or a Gherkin file without importing/exporting."""
    from archledger.bdd.validate import (
        validate_bdd_all,
        validate_bdd_feature_file,
        validate_bdd_record,
    )
    from archledger.cli import _run_configured_command, _state
    from archledger.cli_payloads import bdd_validate_payload

    state = _state(ctx)
    if not record_id and not feature_file and not all_records:
        raise ArchledgerError("Provide a RECORD_ID, --feature-file, or --all.")
    if sum(bool(x) for x in (record_id, feature_file, all_records)) > 1:
        raise ArchledgerError("Pass only one of RECORD_ID, --feature-file, or --all.")

    def _build(repo, paths, config):  # noqa: ANN001
        del paths, config
        if feature_file:
            response = validate_bdd_feature_file(repo, feature_file)
        elif all_records:
            response = validate_bdd_all(repo)
        else:
            response = validate_bdd_record(repo, record_id or "")
        return bdd_validate_payload(response)

    def _fmt(p: dict[str, object]) -> str:
        findings = p.get("findings", [])
        if not findings:
            return f"{p.get('target')}: valid."
        lines = [f"{p.get('target')}: {'INVALID' if not p.get('valid') else 'valid'}"]
        for f in findings:
            loc = ""
            if f.get("line"):
                loc = f" (line {f.get('line')})"
            lines.append(
                f"  [{f.get('severity')}] {f.get('code')}: {f.get('message')}{loc}"
            )
        return "\n".join(lines)

    _run_configured_command(state, "bdd validate", _build, _fmt)


@bdd_app.command("list")
def list_command(
    ctx: typer.Context,
    status: Annotated[
        str | None,
        typer.Option("--status", help="Filter by record status."),
    ] = None,
    automation: Annotated[
        str | None,
        typer.Option("--automation", help="Filter by automation status."),
    ] = None,
    feature: Annotated[
        str | None,
        typer.Option("--feature", help="Filter by feature name."),
    ] = None,
) -> None:
    """List records with bdd metadata and automation status."""
    from archledger.bdd.inspect import list_bdd_records
    from archledger.cli import _run_configured_command, _state
    from archledger.cli_payloads import bdd_list_payload

    state = _state(ctx)

    def _build(repo, paths, config):  # noqa: ANN001
        del paths, config
        response = list_bdd_records(
            repo,
            status_filter=status,
            automation_filter=automation,
            feature_filter=feature,
        )
        return bdd_list_payload(response)

    def _fmt(p: dict[str, object]) -> str:
        entries = p.get("entries", [])
        if not entries:
            return "No records with bdd metadata."
        lines = [f"BDD records ({p.get('count')}):"]
        for e in entries:
            lines.append(
                f"  {e.get('record_id')} [{e.get('status')}] "
                f"{e.get('feature')} / {e.get('scenario')} "
                f"(automation: {e.get('automation_status') or 'none'})"
            )
        return "\n".join(lines)

    _run_configured_command(state, "bdd list", _build, _fmt)


@bdd_app.command("status")
def status_command(ctx: typer.Context) -> None:
    """Summarize BDD coverage (GWT, linked features, automation)."""
    from archledger.bdd.inspect import bdd_status_summary
    from archledger.cli import _run_configured_command, _state
    from archledger.cli_payloads import bdd_status_payload

    state = _state(ctx)

    def _build(repo, paths, config):  # noqa: ANN001
        del paths, config
        response = bdd_status_summary(repo)
        return bdd_status_payload(response)

    def _fmt(p: dict[str, object]) -> str:
        totals = p.get("totals", {})
        coverage = p.get("coverage", {})
        lines = [f"BDD examples: {totals.get('examples', 0)}"]
        for key in ("complete_gwt", "linked_feature_files", "automated", "pending"):
            dim = coverage.get(key, {})
            lines.append(f"  {key}: {dim.get('covered', 0)}/{dim.get('total', 0)}")
        lines.append(f"  invalid_metadata: {totals.get('invalid_metadata', 0)}")
        return "\n".join(lines)

    _run_configured_command(state, "bdd status", _build, _fmt)


@bdd_app.command("set")
def set_command(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument(help="Record to set bdd metadata on.")],
    feature: Annotated[str | None, typer.Option("--feature")] = None,
    rule: Annotated[str | None, typer.Option("--rule")] = None,
    scenario: Annotated[str | None, typer.Option("--scenario")] = None,
    given: Annotated[list[str] | None, typer.Option("--given")] = None,
    when: Annotated[list[str] | None, typer.Option("--when")] = None,
    then: Annotated[list[str] | None, typer.Option("--then")] = None,
    tag: Annotated[list[str] | None, typer.Option("--tag")] = None,
    ac: Annotated[list[str] | None, typer.Option("--ac")] = None,
    task: Annotated[list[str] | None, typer.Option("--task")] = None,
    automation_status: Annotated[
        str | None,
        typer.Option("--automation-status", help="Set automation.status."),
    ] = None,
    feature_file: Annotated[
        str | None,
        typer.Option("--feature-file", help="Set automation.feature_file."),
    ] = None,
    cli_command: Annotated[
        str | None,
        typer.Option("--command", help="Set automation.command (never executed)."),
    ] = None,
) -> None:
    """Create or replace the bdd block on a record without manual YAML edits."""
    from archledger.cli import _find_record_path, _state, _validate_mutation
    from archledger.cli import _run_configured_command as _run
    from archledger.mutations import set_record_meta
    from archledger.storage.frontmatter import read_front_matter_document

    state = _state(ctx)

    def _build(repo, paths, config):  # noqa: ANN001
        del config
        target_path = _find_record_path(repo, record_id)
        metadata, _body = read_front_matter_document(target_path)
        existing = metadata.get("bdd")
        base = dict(existing) if isinstance(existing, dict) else {}

        if feature is not None:
            base["feature"] = feature
        if rule is not None:
            base["rule"] = rule
        if scenario is not None:
            base["scenario"] = scenario
        if given is not None:
            base["given"] = list(given)
        if when is not None:
            base["when"] = list(when)
        if then is not None:
            base["then"] = list(then)
        if tag is not None:
            base["tags"] = list(tag)
        if ac is not None:
            base["acceptance_criteria"] = list(ac)
        if task is not None:
            base["task_refs"] = list(task)

        auto = (
            dict(base.get("automation", {}))
            if isinstance(base.get("automation"), dict)
            else {}
        )
        if automation_status is not None:
            auto["status"] = automation_status
        if feature_file is not None:
            auto["feature_file"] = feature_file
        if cli_command is not None:
            auto["command"] = cli_command
        if auto:
            base["automation"] = auto

        set_record_meta(
            target_path,
            record_id,
            "bdd",
            base,
            workspace_root=paths.workspace_root,
        )
        _validate_mutation(repo, target_path)
        return {"id": record_id, "bdd": base}

    def _fmt(p: dict[str, object]) -> str:
        return f"Set bdd metadata on {p.get('id')}."

    _run(state, "bdd set", _build, _fmt)


@bdd_app.command("link")
def link_command(
    ctx: typer.Context,
    record_id: Annotated[str, typer.Argument(help="Record to link automation to.")],
    feature_file: Annotated[
        str | None,
        typer.Option(
            "--feature-file",
            help="Feature file path (relative POSIX inside workspace).",
        ),
    ] = None,
    link_scenario: Annotated[
        str | None,
        typer.Option("--scenario", help="Scenario name in the feature file."),
    ] = None,
    cli_command: Annotated[
        str | None,
        typer.Option("--command", help="Runner command (never executed)."),
    ] = None,
    link_status: Annotated[
        str | None,
        typer.Option(
            "--status",
            help="Automation status (linked|automated|pending|not_applicable).",
        ),
    ] = None,
) -> None:
    """Link automation metadata and source_refs without executing anything."""
    from archledger.cli import _find_record_path, _state, _validate_mutation
    from archledger.cli import _run_configured_command as _run
    from archledger.mutations import add_source_ref, set_record_meta
    from archledger.storage.frontmatter import read_front_matter_document

    state = _state(ctx)

    def _build(repo, paths, config):  # noqa: ANN001
        del config
        target_path = _find_record_path(repo, record_id)
        metadata, _body = read_front_matter_document(target_path)
        existing = metadata.get("bdd")
        if not isinstance(existing, dict):
            raise ArchledgerError(
                f"Record {record_id} has no bdd metadata. Run 'bdd set' first."
            )

        auto = dict(existing.get("automation", {}))
        if feature_file is not None:
            auto["feature_file"] = feature_file
        if link_scenario is not None:
            auto["scenario"] = link_scenario
        if cli_command is not None:
            auto["command"] = cli_command
        if link_status is not None:
            auto["status"] = link_status
        elif feature_file and auto.get("status") in ("pending", "", None):
            # Auto-advance to linked when a feature file is provided.
            auto["status"] = "linked"
        existing["automation"] = auto

        set_record_meta(
            target_path,
            record_id,
            "bdd",
            existing,
            workspace_root=paths.workspace_root,
        )

        # Also add a source_ref with role=documents for the feature file.
        if feature_file:
            add_source_ref(
                target_path,
                record_id,
                feature_file,
                role="documents",
                reason="Linked Gherkin feature file.",
                workspace_root=paths.workspace_root,
            )

        _validate_mutation(repo, target_path)
        return {"id": record_id, "automation": auto}

    def _fmt(p: dict[str, object]) -> str:
        auto = p.get("automation", {})
        return (
            f"Linked {p.get('id')}: "
            f"automation.status={auto.get('status')} "
            f"feature_file={auto.get('feature_file', '')}"
        )

    _run(state, "bdd link", _build, _fmt)


@bdd_app.command("sync")
def sync_command(
    ctx: typer.Context,
    check: Annotated[
        bool,
        typer.Option(
            "--check", help="Check for drift between feature files and record metadata."
        ),
    ] = False,
) -> None:
    """Compare feature files against record metadata and report drift."""
    from archledger.bdd.sync import check_bdd_sync
    from archledger.cli import _run_configured_command, _state
    from archledger.cli_payloads import bdd_sync_payload

    state = _state(ctx)
    if not check:
        raise ArchledgerError("Pass --check to compare feature files against records.")

    def _build(repo, paths, config):  # noqa: ANN001
        del paths, config
        response = check_bdd_sync(repo)
        return bdd_sync_payload(response)

    def _fmt(p):
        findings = p.get("findings", [])
        if not findings:
            return (
                f"Checked {p.get('checked', 0)} record(s) against "
                f"{p.get('feature_files_checked', 0)} feature file(s): no drift."
            )
        lines = [
            f"BDD sync: {len(findings)} finding(s) across "
            f"{p.get('checked', 0)} record(s):"
        ]
        for f in findings:
            lines.append(f"  [{f.get('severity')}] {f.get('code')}: {f.get('message')}")
        return "\n".join(lines)

    _run_configured_command(state, "bdd sync", _build, _fmt)


__all__ = ["bdd_app"]
