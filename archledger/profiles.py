"""Profile operations for architecture documentation profiles."""

from __future__ import annotations

import dataclasses
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found]

from archledger.config.model import DEFAULT_ARC42_SECTIONS_DIR, VALID_PROFILES
from archledger.config.parse import load_project_config
from archledger.config.render import render_project_config
from archledger.errors import ArchledgerError, ConfigError
from archledger.storage.common import ensure_dir, read_text, write_text_atomic


@dataclass(frozen=True, slots=True)
class ProfileMigrationStep:
    """One step performed (or planned) during a profile migration."""

    action: str
    source: str | None = None
    target: str | None = None
    message: str = ""


@dataclass(frozen=True, slots=True)
class ProfileMigrationResult:
    """Outcome of ``profile migrate`` / ``profile enable`` / ``profile disable``."""

    profile: str
    write: bool
    changed: bool
    steps: tuple[ProfileMigrationStep, ...]
    warnings: tuple[str, ...] = ()


def _read_toml(path: Path) -> dict[str, object]:
    try:
        return cast("dict[str, object]", tomllib.loads(read_text(path)))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Failed to parse {path.name}: {exc}") from exc


def _find_legacy_sections_dir(archledger_dir: Path) -> Path:
    return archledger_dir / "sections"


def _find_profile_sections_dir(archledger_dir: Path) -> Path:
    return archledger_dir / "profiles" / "arc42" / "sections"


def _ensure_profiles_block(
    lines: list[str],
    *,
    default: str,
    enabled: tuple[str, ...],
) -> list[str]:
    profiles_lines = _render_profiles_block(default=default, enabled=enabled)
    cleaned: list[str] = []
    skipping = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[profiles"):
            skipping = True
            continue
        if (
            skipping
            and stripped.startswith("[")
            and not stripped.startswith("[profiles")
        ):
            skipping = False
        if skipping:
            continue
        cleaned.append(line)
    cleaned.append("")
    cleaned.extend(profiles_lines)
    return cleaned


def _render_profiles_block(*, default: str, enabled: tuple[str, ...]) -> list[str]:
    lines = ["[profiles]", "enabled = ["]
    for name in enabled:
        lines.append(f"  {json.dumps(name)},")
    lines.append("]")
    lines.append(f"default = {json.dumps(default)}")
    lines.append("")
    lines.append("[profiles.arc42]")
    lines.append('kind = "documentation"')
    lines.append('template = "arc42"')
    lines.append(f'sections_dir = "{DEFAULT_ARC42_SECTIONS_DIR}"')
    lines.append('build_template = "arc42_document"')
    lines.append("include_help = false")
    lines.append("")
    return lines


def migrate_arc42_profile(
    config_path: Path,
    archledger_dir: Path,
    *,
    write: bool,
) -> ProfileMigrationResult:
    """Migrate a legacy arc42-only project to the profile layout."""
    steps: list[ProfileMigrationStep] = []
    warnings: list[str] = []
    changed = False

    raw = _read_toml(config_path)
    config_version = raw.get("config_version")
    if isinstance(config_version, bool) or not isinstance(config_version, int):
        raise ConfigError("config_version must be an integer.")
    profiles_present = isinstance(raw.get("profiles"), dict)

    legacy_sections = _find_legacy_sections_dir(archledger_dir)
    profile_sections = _find_profile_sections_dir(archledger_dir)

    needs_sections_move = legacy_sections.is_dir() and not profile_sections.is_dir()
    if needs_sections_move:
        steps.append(
            ProfileMigrationStep(
                action="move_sections",
                source=str(legacy_sections),
                target=str(profile_sections),
                message=(f"Move {legacy_sections} -> {profile_sections}"),
            )
        )
    elif legacy_sections.is_dir() and profile_sections.is_dir():
        warnings.append(
            f"Both {legacy_sections} and {profile_sections} exist; leaving "
            "the legacy directory in place."
        )

    if profiles_present and config_version >= 8:
        steps.append(
            ProfileMigrationStep(
                action="noop_config",
                message="Config already has a [profiles] table at config_version >= 8.",
            )
        )
    else:
        steps.append(
            ProfileMigrationStep(
                action="rewrite_config",
                source=str(config_path),
                message=(
                    "Bump config_version to 8 and add [profiles]/[profiles.arc42]."
                ),
            )
        )

    if not write:
        return ProfileMigrationResult(
            profile="arc42",
            write=False,
            changed=needs_sections_move
            or not (profiles_present and config_version >= 8),
            steps=tuple(steps),
            warnings=tuple(warnings),
        )

    if needs_sections_move:
        ensure_dir(profile_sections.parent)
        legacy_sections.rename(profile_sections)
        changed = True

    if not (profiles_present and config_version >= 8):
        original_text = read_text(config_path)
        lines = original_text.splitlines()
        for index, line in enumerate(lines):
            if line.strip().startswith("config_version"):
                lines[index] = "config_version = 8"
                break
        else:
            lines.insert(0, "config_version = 8")
        lines = _ensure_profiles_block(lines, default="arc42", enabled=("arc42",))
        new_text = "\n".join(lines).rstrip() + "\n"
        write_text_atomic(config_path, new_text)
        changed = True

    return ProfileMigrationResult(
        profile="arc42",
        write=True,
        changed=changed,
        steps=tuple(steps),
        warnings=tuple(warnings),
    )


def _check_profile_supported(profile: str) -> None:
    if profile == "sdd":
        raise ArchledgerError(
            "Profile 'sdd' has been removed from archledger. "
            "SDD orchestration belongs in ledgerdeck."
        )
    if profile == "bdd":
        raise ArchledgerError(
            "Profile 'bdd' is not supported by archledger. "
            "BDD/Gherkin belongs in the behavior ledger/tool and is coordinated "
            "by ledgerdeck."
        )
    if profile not in VALID_PROFILES:
        raise ArchledgerError(
            f"profile must be one of: {', '.join(sorted(VALID_PROFILES))}."
        )


def enable_profile(
    config_path: Path,
    archledger_dir: Path,
    profile: str,
    *,
    write: bool = True,
) -> ProfileMigrationResult:
    """Enable a profile in the project config."""
    del archledger_dir
    _check_profile_supported(profile)
    config = load_project_config(config_path)
    if profile in config.profiles.profiles.enabled:
        return ProfileMigrationResult(
            profile=profile,
            write=write,
            changed=False,
            steps=(
                ProfileMigrationStep(
                    action="noop",
                    message=f"Profile '{profile}' is already enabled.",
                ),
            ),
        )
    new_config = dataclasses.replace(
        config,
        config_version=8,
        profiles_present=True,
        profiles=dataclasses.replace(
            config.profiles,
            profiles=dataclasses.replace(
                config.profiles.profiles,
                enabled=tuple(
                    dict.fromkeys((*config.profiles.profiles.enabled, profile))
                ),
            ),
        ),
    )
    if write:
        write_text_atomic(config_path, render_project_config(new_config))
    return ProfileMigrationResult(
        profile=profile,
        write=write,
        changed=True,
        steps=(
            ProfileMigrationStep(
                action="enable_profile",
                message=f"Add '{profile}' to profiles.enabled.",
            ),
        ),
    )


def disable_profile(
    config_path: Path,
    profile: str,
    *,
    write: bool = True,
) -> ProfileMigrationResult:
    """Disable a profile in the project config."""
    _check_profile_supported(profile)
    config = load_project_config(config_path)
    enabled = list(config.profiles.profiles.enabled)
    if profile not in enabled:
        return ProfileMigrationResult(
            profile=profile,
            write=write,
            changed=False,
            steps=(
                ProfileMigrationStep(
                    action="noop",
                    message=f"Profile '{profile}' is not enabled.",
                ),
            ),
        )
    if len(enabled) == 1:
        raise ArchledgerError("Cannot disable the last enabled profile.")
    enabled = [name for name in enabled if name != profile]
    default = config.profiles.profiles.default
    if default == profile:
        default = enabled[0]
    new_config = dataclasses.replace(
        config,
        config_version=8,
        profiles_present=True,
        profiles=dataclasses.replace(
            config.profiles,
            profiles=dataclasses.replace(
                config.profiles.profiles,
                enabled=tuple(enabled),
                default=default,
            ),
        ),
    )
    if write:
        write_text_atomic(config_path, render_project_config(new_config))
    return ProfileMigrationResult(
        profile=profile,
        write=write,
        changed=True,
        steps=(
            ProfileMigrationStep(
                action="disable_profile",
                message=f"Remove '{profile}' from profiles.enabled.",
            ),
        ),
    )


def list_profiles(
    config_path: Path,
    archledger_dir: Path,
) -> dict[str, object]:
    """Return a summary of enabled/default profiles for a project."""
    del archledger_dir
    config = load_project_config(config_path)
    known = sorted(VALID_PROFILES)
    enabled = list(config.profiles.profiles.enabled)
    return {
        "known": known,
        "enabled": enabled,
        "default": config.profiles.profiles.default,
        "available": [name for name in known if name not in enabled],
        "profiles": {
            "arc42": True,
        },
    }


__all__ = [
    "ProfileMigrationResult",
    "ProfileMigrationStep",
    "disable_profile",
    "enable_profile",
    "list_profiles",
    "migrate_arc42_profile",
]
