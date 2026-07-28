"""Typer boundary for Ledgerwerk-family CLI contracts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

import typer
from ledgercore.cli import (
    CLIError,
    CLIWarning,
    CommonCLIState,
    ErrorEnvelope,
    ExitCode,
    SuccessEnvelope,
)

from archledger.errors import ArchledgerError

_ERROR_CODE_BY_TYPE = {
    "ConfigError": "configuration_invalid",
    "StorageError": "storage_conflict",
    "ValidationError": "validation_failed",
    "FrontMatterError": "configuration_invalid",
    "RenderError": "external_dependency_failed",
}


def warning_from_value(value: object) -> CLIWarning:
    """Normalize legacy warning strings and structured warning values."""
    if isinstance(value, CLIWarning):
        return value
    if isinstance(value, Mapping):
        return CLIWarning(
            code=str(value.get("code", "warning")),
            message=str(value.get("message", value)),
            replacement=(
                str(value["replacement"]) if value.get("replacement") else None
            ),
        )
    return CLIWarning(code="warning", message=str(value))


def warnings_from_values(values: Iterable[object]) -> tuple[CLIWarning, ...]:
    """Normalize a command's warning collection for both output modes."""
    return tuple(warning_from_value(value) for value in values)


def _canonical_error_code(exc: ArchledgerError) -> str:
    raw = exc.details.get("code") or exc.details.get("domain_code")
    if isinstance(raw, str) and raw and raw.islower() and " " not in raw:
        return raw
    if type(exc).__name__ == "StorageError" and not raw:
        return "domain_failure"
    return _ERROR_CODE_BY_TYPE.get(type(exc).__name__, "validation_failed")


def cli_error_from_archledger(exc: ArchledgerError) -> CLIError:
    """Translate a domain exception into Ledgercore's CLI error model."""
    details = dict(exc.details)
    raw_code = details.pop("code", None) or details.pop("domain_code", None)
    if isinstance(raw_code, str) and raw_code.isupper():
        details.setdefault("domain_code", raw_code)
    remediation = details.pop("remediation", ())
    if isinstance(remediation, str):
        remediation = (remediation,)
    elif not isinstance(remediation, tuple):
        remediation = tuple(remediation) if remediation else ()
    details.setdefault("type", type(exc).__name__)
    return CLIError(
        code=_canonical_error_code(exc),
        message=exc.message,
        remediation=tuple(str(item) for item in remediation),
        details=details,
    )


def emit_success(
    state: CommonCLIState,
    *,
    command: str,
    result: Mapping[str, object],
    warnings: Iterable[object],
    human_message: str,
) -> None:
    """Emit one deterministic Ledgerwerk success envelope or human result."""
    normalized_warnings = warnings_from_values(warnings)
    if state.json_output:
        envelope = SuccessEnvelope(
            tool=state.tool,
            command=command,
            result=_normalize_json_paths(result),
            warnings=normalized_warnings,
        )
        typer.echo(envelope.to_json())
        return

    typer.echo(human_message)
    if not state.quiet:
        for warning in normalized_warnings:
            typer.echo(f"warning: {warning.message}", err=True)


def emit_error(
    state: CommonCLIState,
    command: str,
    exc: ArchledgerError,
    *,
    exit_code: ExitCode | int | None = None,
) -> None:
    """Emit one deterministic Ledgerwerk error envelope and exit."""
    error = cli_error_from_archledger(exc)
    selected_exit = exit_code if exit_code is not None else _exit_code_for(error)
    if state.json_output:
        envelope = ErrorEnvelope(
            tool=state.tool,
            command=command,
            error={
                "code": error.code,
                "type": error.details.get("type"),
                "message": error.message,
                "remediation": list(error.remediation),
                "details": {
                    key: value for key, value in error.details.items() if key != "type"
                },
            },
        )
        typer.echo(envelope.to_json())
    else:
        typer.echo(f"{error.code}: {error.message}", err=True)
        for remediation in error.remediation:
            typer.echo(f"  hint: {remediation}", err=True)
    raise typer.Exit(code=int(selected_exit))


def _exit_code_for(error: CLIError) -> ExitCode:
    if error.code in {"invalid_arguments", "configuration_invalid"}:
        return ExitCode.USAGE
    if error.code in {"archledger_uninitialized", "record_not_found"}:
        return ExitCode.UNAVAILABLE
    if error.code in {
        "migration_plan_stale",
        "storage_conflict",
        "storage_migration_locked",
    }:
        return ExitCode.CONFLICT
    if error.code == "external_dependency_failed":
        # Preserve Archledger's established domain-failure exit code while
        # retaining the precise dependency code in the envelope.
        return ExitCode.DOMAIN_FAILURE
    return ExitCode.DOMAIN_FAILURE


def _normalize_json_paths(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _normalize_json_paths(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_json_paths(item) for item in value]
    return value


__all__ = [
    "CLIError",
    "CLIWarning",
    "CommonCLIState",
    "ErrorEnvelope",
    "ExitCode",
    "SuccessEnvelope",
    "cli_error_from_archledger",
    "emit_error",
    "emit_success",
    "warning_from_value",
    "warnings_from_values",
]
