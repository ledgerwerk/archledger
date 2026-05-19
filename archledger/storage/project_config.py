from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from archledger.errors import ConfigError
from archledger.storage.common import read_text

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib


_ALLOWED_TOP_LEVEL_KEYS = {
    "config_version",
    "archledger_dir",
    "project_uuid",
    "project_name",
    "build",
    "arc42",
}
_ALLOWED_BUILD_KEYS = {"default_output", "include_draft", "strict"}
_ALLOWED_ARC42_KEYS = {"template_version", "language", "title"}


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    config_version: int
    archledger_dir: str
    project_uuid: str
    project_name: str
    build_default_output: str = "architecture.md"
    build_include_draft: bool = False
    build_strict: bool = False
    arc42_template_version: str = "9.0-EN"
    arc42_language: str = "en"
    arc42_title: str = "Architecture Documentation"


def normalize_project_name(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", name.strip().lower()).strip("-")
    if not normalized:
        raise ConfigError("Project name must contain at least one letter or number.")
    return normalized


def render_default_config(
    workspace_root: Path,
    *,
    archledger_dir: str,
    project_name: str | None = None,
    project_uuid: str | None = None,
) -> str:
    normalized_project_name = normalize_project_name(
        workspace_root.name if project_name is None else project_name
    )
    normalized_uuid = (
        str(uuid4()) if project_uuid is None else _validate_uuid(project_uuid)
    )
    return "\n".join(
        [
            "# Project-local archledger configuration.",
            "# This file lives in the source project root.",
            "config_version = 1",
            f'archledger_dir = "{archledger_dir}"',
            "",
            "# Stable project identity. Commit this with your source tree.",
            f'project_uuid = "{normalized_uuid}"',
            f'project_name = "{normalized_project_name}"',
            "",
            "[build]",
            'default_output = "architecture.md"',
            "include_draft = false",
            "strict = false",
            "",
            "[arc42]",
            'template_version = "9.0-EN"',
            'language = "en"',
            'title = "Architecture Documentation"',
            "",
        ]
    )


def load_project_config(path: Path) -> ProjectConfig:
    try:
        raw_data = tomllib.loads(read_text(path))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Failed to parse {path.name}: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise ConfigError(f"{path.name} did not parse to a TOML table.")

    unknown_top_level = sorted(set(raw_data) - _ALLOWED_TOP_LEVEL_KEYS)
    if unknown_top_level:
        joined = ", ".join(unknown_top_level)
        raise ConfigError(f"Unknown config keys in {path.name}: {joined}")

    build_data = _validate_subtable(
        path,
        raw_data.get("build"),
        _ALLOWED_BUILD_KEYS,
        "build",
    )
    arc42_data = _validate_subtable(
        path,
        raw_data.get("arc42"),
        _ALLOWED_ARC42_KEYS,
        "arc42",
    )

    config_version = raw_data.get("config_version")
    if config_version != 1:
        raise ConfigError("config_version must be 1.")

    archledger_dir = raw_data.get("archledger_dir")
    if not isinstance(archledger_dir, str) or not archledger_dir.strip():
        raise ConfigError("archledger_dir must be a non-empty string.")

    project_uuid = raw_data.get("project_uuid")
    if not isinstance(project_uuid, str):
        raise ConfigError("project_uuid must be a string.")

    project_name = raw_data.get("project_name")
    if not isinstance(project_name, str):
        raise ConfigError("project_name must be a string.")

    default_output = build_data.get("default_output", "architecture.md")
    if not isinstance(default_output, str) or not default_output.strip():
        raise ConfigError("build.default_output must be a non-empty string.")

    include_draft = build_data.get("include_draft", False)
    strict = build_data.get("strict", False)
    if not isinstance(include_draft, bool) or not isinstance(strict, bool):
        raise ConfigError("build.include_draft and build.strict must be booleans.")

    template_version = arc42_data.get("template_version", "9.0-EN")
    language = arc42_data.get("language", "en")
    title = arc42_data.get("title", "Architecture Documentation")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (template_version, language, title)
    ):
        raise ConfigError(
            "arc42.template_version, arc42.language, and arc42.title "
            "must be non-empty strings."
        )

    return ProjectConfig(
        config_version=1,
        archledger_dir=archledger_dir,
        project_uuid=_validate_uuid(project_uuid),
        project_name=normalize_project_name(project_name),
        build_default_output=default_output,
        build_include_draft=include_draft,
        build_strict=strict,
        arc42_template_version=cast(str, template_version),
        arc42_language=cast(str, language),
        arc42_title=cast(str, title),
    )


def _validate_subtable(
    path: Path,
    value: object,
    allowed_keys: set[str],
    table_name: str,
) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{table_name} in {path.name} must be a TOML table.")
    unknown_keys = sorted(set(value) - allowed_keys)
    if unknown_keys:
        joined = ", ".join(unknown_keys)
        raise ConfigError(f"Unknown keys in {table_name}: {joined}")
    return dict(value)


def _validate_uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ConfigError("project_uuid must be a valid UUID.") from exc
