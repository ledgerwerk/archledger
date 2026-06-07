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

from archledger.errors import ArchledgerError

bdd_app = typer.Typer(add_completion=False, no_args_is_help=True)


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
) -> None:
    """Import a Gherkin feature file into archledger as behavior records."""
    from archledger.bdd.importer import BddImportResponse, import_bdd_feature
    from archledger.cli import _run_configured_command, _state
    from archledger.cli_payloads import bdd_import_payload

    state = _state(ctx)

    def _build_import_result(repo, paths, config):  # noqa: ANN001
        del paths, config
        try:
            response: BddImportResponse = import_bdd_feature(
                repo,
                feature_file,
                kind=kind,
                status=status,
                section=section,
            )
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
        str,
        typer.Argument(help="Archledger record ID to export."),
    ],
    out: Annotated[
        str,
        typer.Option(
            "--out",
            help="Output .feature file path.",
        ),
    ],
) -> None:
    """Export an archledger record with bdd metadata as a Gherkin feature file."""
    from archledger.bdd.exporter import export_bdd_record
    from archledger.cli import _run_configured_command, _state
    from archledger.cli_payloads import bdd_export_payload

    state = _state(ctx)

    def _build_export_result(repo, paths, config):  # noqa: ANN001
        del config
        try:
            response = export_bdd_record(
                repo,
                record_id,
                out,
            )
        except (ValueError, FileNotFoundError, ArchledgerError) as exc:
            raise ArchledgerError(str(exc)) from exc
        return bdd_export_payload(response)

    _run_configured_command(
        state,
        "bdd export",
        _build_export_result,
        lambda p: f"Exported {p['record_id']} to {p['output_file']}",
    )


__all__ = ["bdd_app"]
