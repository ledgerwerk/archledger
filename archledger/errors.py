from __future__ import annotations


class ArchledgerError(Exception):
    """Base exception for archledger failures."""

    def __init__(
        self,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = {} if details is None else dict(details)


class ConfigError(ArchledgerError):
    """Raised when project configuration is missing or invalid."""


class StorageError(ArchledgerError):
    """Raised when the archledger storage layout is invalid."""


class FrontMatterError(ArchledgerError):
    """Raised when Markdown front matter cannot be parsed or written."""


class ValidationError(ArchledgerError):
    """Raised when records or configuration fail validation."""


class RenderError(ArchledgerError):
    """Raised when document rendering fails."""
