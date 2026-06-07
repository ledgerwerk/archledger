"""Profile operations: arc42/sdd enable, disable, and legacy migration.

The repository delegates profile-level mutations here so that
``repository.py`` stays focused on record storage and structural
validation.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path

import tomllib

from archledger.config.model import (
    DEFAULT_ARC42_SECTIONS_DIR,
    VALID_PROFILES,
)
from archledger.config.parse import (
    load_project_config,
)
from archledger.config.render import (
    render_project_config,
)
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
        return tomllib.loads(read_text(path))
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
    include_sdd: bool,
) -> list[str]:
    """Return a copy of ``lines`` with a [profiles] block inserted/replaced.

    This is a best-effort textual transform used by ``profile migrate`` so we
    do not have to round-trip the entire config through the dataclass model
    (which would normalise unrelated formatting).
    """
    profiles_lines = _render_profiles_block(
        default=default, enabled=enabled, include_sdd=include_sdd
    )
    # Drop any existing [profiles]/[profiles.*] blocks.
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


def _render_profiles_block(
    *, default: str, enabled: tuple[str, ...], include_sdd: bool
) -> list[str]:
    import json

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
    if include_sdd or "sdd" in enabled or default == "sdd":
        lines.append("[profiles.sdd]")
        lines.append('kind = "contract"')
        lines.append("require_acceptance_criteria = true")
        lines.append("require_implementation_refs = true")
        lines.append("require_test_refs = true")
        lines.append("require_bdd_gwt_for_behavior_records = true")
        lines.append("require_bdd_automation_for_accepted_records = false")
        lines.append("")
    return lines


def migrate_arc42_profile(
    config_path: Path,
    archledger_dir: Path,
    *,
    write: bool,
) -> ProfileMigrationResult:
    """Migrate a legacy arc42-only project to the profile layout.

    Steps:
      1. Detect legacy ``<archledger_dir>/sections/``.
      2. Move it to ``<archledger_dir>/profiles/arc42/sections/``.
      3. Rewrite ``archledger.toml``: bump ``config_version`` to 8 and add
         ``[profiles]`` / ``[profiles.arc42]``.
      4. Leave ``<archledger_dir>/records/**`` untouched.
    """
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

    # Apply.
    if needs_sections_move:
        ensure_dir(profile_sections.parent)
        legacy_sections.rename(profile_sections)
        changed = True

    if not (profiles_present and config_version >= 8):
        original_text = read_text(config_path)
        lines = original_text.splitlines()
        # Bump config_version.
        for index, line in enumerate(lines):
            if line.strip().startswith("config_version"):
                lines[index] = "config_version = 8"
                break
        else:
            lines.insert(0, "config_version = 8")
        lines = _ensure_profiles_block(
            lines, default="arc42", enabled=("arc42",), include_sdd=False
        )
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


def enable_profile(
    config_path: Path,
    archledger_dir: Path,
    profile: str,
    *,
    write: bool = True,
) -> ProfileMigrationResult:
    """Enable a profile (arc42 or sdd) in the project config."""
    if profile == "bdd":
        raise ArchledgerError(
            "BDD is not a standalone profile. Enable the SDD profile and use "
            "`archledger bdd import/export`. Run: archledger profile enable sdd"
        )
    if profile not in VALID_PROFILES:
        raise ArchledgerError(
            f"profile must be one of: {', '.join(sorted(VALID_PROFILES))}."
        )
    raw = _read_toml(config_path)
    profiles_table = raw.get("profiles")
    if isinstance(profiles_table, dict):
        enabled_raw = profiles_table.get("enabled", ["arc42"])
        default_raw = profiles_table.get("default", "arc42")
    else:
        enabled_raw = ["arc42"]
        default_raw = "arc42"
    if not isinstance(enabled_raw, list):
        raise ConfigError("profiles.enabled must be a list of strings.")
    if not isinstance(default_raw, str):
        raise ConfigError("profiles.default must be a string.")
    enabled = [str(item) for item in enabled_raw]
    default = str(default_raw)

    steps: list[ProfileMigrationStep] = []
    changed = False
    if profile not in enabled:
        enabled.append(profile)
        changed = True
        steps.append(
            ProfileMigrationStep(
                action="enable_profile",
                message=f"Add '{profile}' to profiles.enabled.",
            )
        )

    if not write:
        return ProfileMigrationResult(
            profile=profile,
            write=False,
            changed=changed,
            steps=tuple(steps),
        )

    if changed:
        config = load_project_config(config_path)
        new_config = dataclasses.replace(
            config,
            config_version=8,
            profiles_present=True,
            profiles=dataclasses.replace(
                config.profiles,
                profiles=dataclasses.replace(
                    config.profiles.profiles,
                    enabled=tuple(dict.fromkeys(enabled)),
                    default=default,
                ),
            ),
        )
        new_text = render_project_config(new_config)
        write_text_atomic(config_path, new_text)
        # Ensure profile directory exists for sdd.
        if profile == "sdd":
            sdd_dir = archledger_dir / "profiles" / "sdd"
            ensure_dir(sdd_dir)

    return ProfileMigrationResult(
        profile=profile,
        write=write,
        changed=changed,
        steps=tuple(steps),
    )


# Boolean policy fields on SddProfileConfig that may be overridden via
# `sdd policy set` / `sdd init --strict-defaults`.
SDD_POLICY_FIELDS: tuple[str, ...] = (
    "require_acceptance_criteria",
    "require_implementation_refs",
    "require_test_refs",
    "require_bdd_gwt_for_behavior_records",
    "require_bdd_automation_for_accepted_records",
)


def ensure_sdd_profile_enabled(
    config_path: Path,
    archledger_dir: Path,
    *,
    write: bool = True,
) -> bool:
    """Ensure the SDD profile is enabled and [profiles.sdd] is present.

    Returns True if a change was made (and written).
    """
    result = enable_profile(config_path, archledger_dir, "sdd", write=write)
    return result.changed and write


def set_sdd_profile_policy(
    config_path: Path,
    archledger_dir: Path,
    overrides: dict[str, bool],
    *,
    write: bool = True,
) -> tuple[dict[str, bool], dict[str, bool]]:
    """Update [profiles.sdd] policy flags and return (before, after).

    Only fields listed in :data:`SDD_POLICY_FIELDS` are accepted. Enables
    the SDD profile first if it is not already enabled.
    """
    invalid = set(overrides) - set(SDD_POLICY_FIELDS)
    if invalid:
        raise ArchledgerError(
            "Unknown SDD policy field(s): " + ", ".join(sorted(invalid))
        )
    config = load_project_config(config_path)
    before = {f: bool(getattr(config.profiles.sdd, f)) for f in SDD_POLICY_FIELDS}
    # Enable sdd if needed so [profiles.sdd] is actually written.
    if "sdd" not in config.profiles.profiles.enabled:
        ensure_sdd_profile_enabled(config_path, archledger_dir, write=write)
        config = load_project_config(config_path)
    new_sdd = dataclasses.replace(config.profiles.sdd, **overrides)
    new_config = dataclasses.replace(
        config,
        config_version=8,
        profiles_present=True,
        profiles=dataclasses.replace(config.profiles, sdd=new_sdd),
    )
    after = {f: bool(getattr(new_sdd, f)) for f in SDD_POLICY_FIELDS}
    if write:
        write_text_atomic(config_path, render_project_config(new_config))
    return before, after


def disable_profile(
    config_path: Path,
    profile: str,
    *,
    write: bool = True,
) -> ProfileMigrationResult:
    """Disable a profile in the project config."""
    if profile == "bdd":
        raise ArchledgerError(
            "BDD is not a standalone profile, so there is nothing to disable."
        )
    if profile not in VALID_PROFILES:
        raise ArchledgerError(
            f"profile must be one of: {', '.join(sorted(VALID_PROFILES))}."
        )
    raw = _read_toml(config_path)
    profiles_table = raw.get("profiles")
    if not isinstance(profiles_table, dict):
        return ProfileMigrationResult(
            profile=profile,
            write=write,
            changed=False,
            steps=(
                ProfileMigrationStep(
                    action="noop",
                    message="No [profiles] table present; nothing to disable.",
                ),
            ),
        )
    enabled_raw = profiles_table.get("enabled", ["arc42"])
    default_raw = profiles_table.get("default", "arc42")
    if not isinstance(enabled_raw, list):
        raise ConfigError("profiles.enabled must be a list of strings.")
    enabled = [str(item) for item in enabled_raw]
    default = str(default_raw)

    steps: list[ProfileMigrationStep] = []
    changed = False
    if profile in enabled:
        if len(enabled) == 1:
            raise ArchledgerError("Cannot disable the last enabled profile.")
        enabled = [name for name in enabled if name != profile]
        changed = True
        steps.append(
            ProfileMigrationStep(
                action="disable_profile",
                message=f"Remove '{profile}' from profiles.enabled.",
            )
        )
    if default == profile and enabled:
        default = enabled[0]
        changed = True
        steps.append(
            ProfileMigrationStep(
                action="reset_default",
                message=(f"profiles.default was '{profile}'; reset to '{default}'."),
            )
        )

    if not write or not changed:
        return ProfileMigrationResult(
            profile=profile,
            write=write,
            changed=changed,
            steps=tuple(steps),
        )
    config = load_project_config(config_path)
    new_config = dataclasses.replace(
        config,
        config_version=8,
        profiles_present=True,
        profiles=dataclasses.replace(
            config.profiles,
            profiles=dataclasses.replace(
                config.profiles.profiles,
                enabled=tuple(dict.fromkeys(enabled)),
                default=default,
            ),
        ),
    )
    new_text = render_project_config(new_config)
    write_text_atomic(config_path, new_text)
    return ProfileMigrationResult(
        profile=profile,
        write=write,
        changed=changed,
        steps=tuple(steps),
    )


def list_profiles(
    config_path: Path,
    archledger_dir: Path,
) -> dict[str, object]:
    """Return a summary of enabled/default profiles for a project."""
    del archledger_dir
    raw = _read_toml(config_path)
    profiles_table = raw.get("profiles")
    if isinstance(profiles_table, dict):
        enabled_raw = profiles_table.get("enabled", ["arc42"])
        default_raw = profiles_table.get("default", "arc42")
        enabled = (
            [str(item) for item in enabled_raw]
            if isinstance(enabled_raw, list)
            else ["arc42"]
        )
        default = str(default_raw) if isinstance(default_raw, str) else "arc42"
    else:
        enabled = ["arc42"]
        default = "arc42"
        profiles_table = {}
    known = sorted(VALID_PROFILES)
    return {
        "known": known,
        "enabled": enabled,
        "default": default,
        "available": [name for name in known if name not in enabled],
        "profiles": {
            "arc42": isinstance(raw.get("profiles"), dict)
            and "arc42" in (profiles_table or {}),
            "sdd": isinstance(raw.get("profiles"), dict)
            and "sdd" in (profiles_table or {}),
        },
    }


__all__ = [
    "ProfileMigrationResult",
    "ProfileMigrationStep",
    "SDD_POLICY_FIELDS",
    "disable_profile",
    "enable_profile",
    "ensure_sdd_profile_enabled",
    "list_profiles",
    "migrate_arc42_profile",
    "set_sdd_profile_policy",
]
