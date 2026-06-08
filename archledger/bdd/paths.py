"""Shared path conventions for Archledger BDD feature files."""

from __future__ import annotations

DEPRECATED_BDD_FEATURE_PATH_PREFIXES: tuple[str, ...] = (
    "tests/bdd/features/",
    "tests/behavior/features/",
    "specs/bdd/features/",
)

RECOMMENDED_BDD_FEATURE_PATH = "specs/behavior/features/<area>/<feature>.feature"


def is_deprecated_bdd_feature_path(path: str) -> bool:
    """Return ``True`` when *path* uses an old feature-file location."""
    return any(
        path.startswith(prefix) for prefix in DEPRECATED_BDD_FEATURE_PATH_PREFIXES
    )


def deprecated_bdd_feature_path_message(path: str) -> str:
    """Explain the preferred behavior-spec location for *path*."""
    return (
        f"{path!r} uses a deprecated BDD feature-file location. "
        f"Prefer {RECOMMENDED_BDD_FEATURE_PATH}."
    )


__all__ = [
    "DEPRECATED_BDD_FEATURE_PATH_PREFIXES",
    "RECOMMENDED_BDD_FEATURE_PATH",
    "deprecated_bdd_feature_path_message",
    "is_deprecated_bdd_feature_path",
]
