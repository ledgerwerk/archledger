"""Shared CLI boundary for Archledger using Ledgerwerk CLI v1 envelope.

This module provides the CommonCLIState, SuccessEnvelope, ErrorEnvelope,
and related primitives for unified JSON emission and exit code mapping.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any

from archledger.errors import ArchledgerError


class ExitCode(IntEnum):
    """Canonical exit codes for Archledger migration commands."""

    SUCCESS = 0
    DOMAIN_VALIDATION_FAILED = 1
    INVALID_COMMAND_OR_OPTIONS = 2
    PROJECT_OR_STATE_UNAVAILABLE = 3
    STALE_OR_CONFLICTING = 4
    EXTERNAL_DEPENDENCY_FAILURE = 5


@dataclass
class CLIWarning:
    """A warning to emit in both human and JSON modes."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CLIError:
    """Structured error for JSON emission."""

    code: str
    message: str
    remediation: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_archledger_error(cls, exc: ArchledgerError) -> CLIError:
        """Create CLIError from ArchledgerError."""
        code = exc.details.get("domain_code", exc.__class__.__name__)
        remediation = exc.details.get("remediation", [])
        if isinstance(remediation, str):
            remediation = [remediation]
        return cls(
            code=code,
            message=exc.message,
            remediation=remediation,
            details={
                k: v
                for k, v in exc.details.items()
                if k not in ("domain_code", "remediation")
            },
        )


@dataclass
class SuccessEnvelope:
    """Ledgerwerk CLI v1 success envelope."""

    schema: str = "ledgerwerk.cli.v1"
    ok: bool = True
    tool: str = "archledger"
    command: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema": self.schema,
            "ok": self.ok,
            "tool": self.tool,
            "command": self.command,
            "result": self.result,
            "events": self.events,
            "warnings": self.warnings,
        }


@dataclass
class ErrorEnvelope:
    """Ledgerwerk CLI v1 error envelope."""

    schema: str = "ledgerwerk.cli.v1"
    ok: bool = False
    tool: str = "archledger"
    command: str = ""
    error: CLIError = field(
        default_factory=lambda: CLIError(code="UNKNOWN", message="Unknown error")
    )
    events: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema": self.schema,
            "ok": self.ok,
            "tool": self.tool,
            "command": self.command,
            "error": {
                "code": self.error.code,
                "message": self.error.message,
                "remediation": self.error.remediation,
                "details": self.error.details,
            },
            "events": self.events,
            "warnings": self.warnings,
        }


@dataclass
class CommonCLIState:
    """Shared CLI state for all commands."""

    root: Path
    json_output: bool = False
    quiet: bool = False
    verbose: bool = False
    warnings: list[CLIWarning] = field(default_factory=list)

    def add_warning(self, code: str, message: str, **details: Any) -> None:
        """Add a warning to the state."""
        self.warnings.append(CLIWarning(code=code, message=message, details=details))


def emit_success(
    state: CommonCLIState,
    *,
    command: str,
    result: dict[str, Any],
    human_message: str,
) -> None:
    """Emit a success response in both JSON and human modes."""
    warnings_data = [
        {"code": w.code, "message": w.message, "details": w.details}
        for w in state.warnings
    ]

    if state.json_output:
        envelope = SuccessEnvelope(
            command=command,
            result=result,
            warnings=warnings_data,
        )
        typer.echo(json.dumps(envelope.to_dict(), indent=2, sort_keys=False))
        return

    typer.echo(human_message)
    for warning in state.warnings:
        if not state.quiet:
            typer.echo(f"warning: {warning.message}", err=True)


def emit_error(
    state: CommonCLIState,
    *,
    command: str,
    exc: ArchledgerError,
    exit_code: ExitCode = ExitCode.DOMAIN_VALIDATION_FAILED,
) -> None:
    """Emit an error response in both JSON and human modes."""
    cli_error = CLIError.from_archledger_error(exc)

    warnings_data = [
        {"code": w.code, "message": w.message, "details": w.details}
        for w in state.warnings
    ]

    if state.json_output:
        envelope = ErrorEnvelope(
            command=command,
            error=cli_error,
            warnings=warnings_data,
        )
        typer.echo(json.dumps(envelope.to_dict(), indent=2, sort_keys=False))
    else:
        typer.echo(f"{cli_error.code}: {cli_error.message}", err=True)
        for remediation in cli_error.remediation:
            typer.echo(f"  hint: {remediation}", err=True)

    raise typer.Exit(code=int(exit_code))


def emit_cli_error(
    state: CommonCLIState,
    *,
    command: str,
    error: CLIError,
    exit_code: ExitCode = ExitCode.DOMAIN_VALIDATION_FAILED,
) -> None:
    """Emit a CLI error response."""
    warnings_data = [
        {"code": w.code, "message": w.message, "details": w.details}
        for w in state.warnings
    ]

    if state.json_output:
        envelope = ErrorEnvelope(
            command=command,
            error=error,
            warnings=warnings_data,
        )
        typer.echo(json.dumps(envelope.to_dict(), indent=2, sort_keys=False))
    else:
        typer.echo(f"{error.code}: {error.message}", err=True)
        for remediation in error.remediation:
            typer.echo(f"  hint: {remediation}", err=True)

    raise typer.Exit(code=int(exit_code))


# typer is used throughout for echo() and Exit()
import typer  # noqa: E402
