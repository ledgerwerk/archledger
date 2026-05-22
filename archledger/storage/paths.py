from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archledger.errors import ConfigError
from archledger.storage.project_config import ProjectConfig, load_project_config

CANONICAL_PROJECT_CONFIG_FILENAME = "archledger.toml"
HIDDEN_PROJECT_CONFIG_FILENAME = ".archledger.toml"
PROJECT_CONFIG_FILENAMES = (
    CANONICAL_PROJECT_CONFIG_FILENAME,
    HIDDEN_PROJECT_CONFIG_FILENAME,
)
DEFAULT_ARCHLEDGER_DIR_NAME = ".archledger"


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    workspace_root: Path
    config_path: Path
    archledger_dir: Path
    sections_dir: Path
    records_dir: Path
    archive_dir: Path
    build_dir: Path
    storage_meta_path: Path
    source_state_path: Path


def discover_project_config(start: Path) -> tuple[Path, list[str]]:
    current = start.resolve()
    if current.is_file():
        current = current.parent

    while True:
        canonical = current / CANONICAL_PROJECT_CONFIG_FILENAME
        hidden = current / HIDDEN_PROJECT_CONFIG_FILENAME
        canonical_exists = canonical.is_file()
        hidden_exists = hidden.is_file()
        if canonical_exists or hidden_exists:
            warnings: list[str] = []
            if canonical_exists and hidden_exists:
                warnings.append(
                    "Both archledger.toml and .archledger.toml exist. "
                    "Using archledger.toml."
                )
            return (canonical if canonical_exists else hidden), warnings
        if current.parent == current:
            break
        current = current.parent

    raise ConfigError("No archledger.toml found. Run: archledger init")


def resolve_project_paths(start: Path) -> tuple[ProjectPaths, ProjectConfig, list[str]]:
    config_path, warnings = discover_project_config(start)
    config = load_project_config(config_path)
    workspace_root = config_path.parent.resolve()
    archledger_dir = _resolve_archledger_dir(workspace_root, config.archledger_dir)
    build_dir = _resolve_relative_child(
        workspace_root,
        config.build_output_dir,
        "build.default_output_dir",
        parent_label="workspace_root",
    )
    source_state_path = _resolve_archledger_child(
        archledger_dir,
        config.tracking_state_file,
        "tracking.state_file",
    )
    _resolve_relative_child(
        build_dir,
        config.build_default_output,
        "build.default_output",
        parent_label="build.default_output_dir",
    )
    _resolve_relative_child(
        build_dir,
        config.diagram_output_dir,
        "diagrams.output_dir",
        parent_label="build.default_output_dir",
    )
    return (
        ProjectPaths(
            workspace_root=workspace_root,
            config_path=config_path.resolve(),
            archledger_dir=archledger_dir,
            sections_dir=archledger_dir / "sections",
            records_dir=archledger_dir / "records",
            archive_dir=archledger_dir / "archive",
            build_dir=build_dir,
            storage_meta_path=archledger_dir / "storage.yaml",
            source_state_path=source_state_path,
        ),
        config,
        warnings,
    )


def _resolve_archledger_dir(workspace_root: Path, archledger_dir: str) -> Path:
    candidate = Path(archledger_dir)
    try:
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            resolved = (workspace_root / candidate).resolve()
    except OSError as exc:
        raise ConfigError(
            f"archledger_dir could not be resolved: {archledger_dir!r}"
        ) from exc

    if not resolved.is_absolute():
        raise ConfigError("archledger_dir did not resolve to an absolute path.")
    return resolved


def _resolve_archledger_child(
    archledger_dir: Path,
    relative_path: str,
    field_name: str,
) -> Path:
    return _resolve_relative_child(
        archledger_dir,
        relative_path,
        field_name,
        parent_label="archledger_dir",
    )


def _resolve_relative_child(
    base_dir: Path,
    relative_path: str,
    field_name: str,
    *,
    parent_label: str,
) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ConfigError(f"{field_name} must be relative to {parent_label}.")
    try:
        resolved = (base_dir / candidate).resolve()
    except OSError as exc:
        raise ConfigError(
            f"{field_name} could not be resolved: {relative_path!r}"
        ) from exc
    try:
        resolved.relative_to(base_dir)
    except ValueError as exc:
        raise ConfigError(f"{field_name} must stay inside {parent_label}.") from exc
    return resolved
