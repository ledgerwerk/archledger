from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

from archledger.config.model import (
    DEFAULT_ARC42_SECTIONS_DIR,
    DEFAULT_ID_SEGMENT,
    DEFAULT_ID_SEGMENT_MAP,
    DEFAULT_TRACKING_EXCLUDE,
    DEFAULT_TRACKING_INCLUDE,
    VALID_BUILD_CONVERTERS,
    VALID_DIAGRAM_IMAGE_FORMATS,
    VALID_DIAGRAM_RENDERERS,
    VALID_DIAGRAM_TYPES,
    VALID_PROFILE_KINDS,
    VALID_PROFILES,
    VALID_TRACKING_HASH_ALGORITHMS,
    VALID_TRACKING_SCANNERS,
    Arc42ProfileConfig,
    ProfilesConfig,
    ProjectConfig,
    ProjectProfilesConfig,
    SddProfileConfig,
    normalize_project_name,
    validate_uuid,
)
from archledger.config.schema import FieldSpec, TableSpec, parse_table_from_spec
from archledger.errors import ConfigError
from archledger.ids import (
    DEFAULT_ID_PREFIX,
    DEFAULT_ID_SEGMENT_MODE,
    DEFAULT_ID_WIDTH,
    validate_id_prefix,
    validate_id_segment,
    validate_id_segment_mode,
    validate_id_width,
)
from archledger.model import (
    CURRENT_SOURCE_SCHEMA_VERSION,
    VALID_OUTPUT_FORMATS,
    VALID_RECORD_TYPES,
    VALID_SOURCE_FORMATS,
    default_document_filename_for_output_format,
    default_extension_for_source_format,
    infer_output_format_from_path,
)
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
    "ids",
    "source",
    "build",
    "arc42",
    "skill",
    "tracking",
    "diagrams",
    "profiles",
}
_ALLOWED_BUILD_KEYS = {
    "default_output",
    "default_format",
    "default_output_dir",
    "include_draft",
    "include_superseded",
    "strict",
    "keep_intermediate",
    "converter",
    "pdf_engine",
    "reference_docx",
    "outputs",
    "diagrams",
}
_ALLOWED_BUILD_OUTPUT_KEYS = {"enabled", "pdf_engine", "reference_docx", "tool"}
_ALLOWED_IDS_KEYS = {
    "prefix",
    "width",
    "segment_mode",
    "default_segment",
    "segment_map",
}
_ALLOWED_ARC42_KEYS = {"template_version", "language", "title", "include_help"}
_ALLOWED_PROFILES_KEYS = {"enabled", "default", "arc42", "sdd"}
_ALLOWED_PROFILES_ARC42_KEYS = {
    "kind",
    "template",
    "sections_dir",
    "build_template",
    "include_help",
}
_ALLOWED_PROFILES_SDD_KEYS = {
    "kind",
    "require_acceptance_criteria",
    "require_implementation_refs",
    "require_test_refs",
}
_ALLOWED_SKILL_KEYS = {"installed", "path"}
_ALLOWED_TRACKING_KEYS = {
    "enabled",
    "state_file",
    "scanner",
    "include",
    "exclude",
    "max_file_bytes",
    "hash_algorithm",
}
_ALLOWED_SOURCE_KEYS = {
    "format",
    "front_matter",
    "section_extension",
    "record_extension",
    "schema_version",
}
_ALLOWED_DIAGRAM_KEYS = {
    "enabled",
    "renderer",
    "default_type",
    "output_dir",
    "image_format",
    "kroki_url",
}
_ALLOWED_BUILD_CONVERTERS = VALID_BUILD_CONVERTERS
_ALLOWED_TRACKING_SCANNERS = VALID_TRACKING_SCANNERS
_ALLOWED_TRACKING_HASH_ALGORITHMS = VALID_TRACKING_HASH_ALGORITHMS
_ALLOWED_DIAGRAM_RENDERERS = VALID_DIAGRAM_RENDERERS
_ALLOWED_DIAGRAM_TYPES = VALID_DIAGRAM_TYPES
_ALLOWED_DIAGRAM_IMAGE_FORMATS = VALID_DIAGRAM_IMAGE_FORMATS


# --- Schema-driven table specs ---


def _parse_tracking_enabled(raw: object, field_name: str) -> bool:
    return _require_bool(raw, field_name)


def _parse_tracking_state_file(raw: object, field_name: str) -> str:
    return _require_non_empty_string(raw, field_name)


def _parse_tracking_scanner(raw: object, field_name: str) -> str:
    return _require_choice(raw, field_name, _ALLOWED_TRACKING_SCANNERS)


def _parse_tracking_include(raw: object, field_name: str) -> tuple[str, ...]:
    return _require_string_tuple(raw, field_name)


def _parse_tracking_exclude(raw: object, field_name: str) -> tuple[str, ...]:
    return _require_string_tuple(raw, field_name)


def _parse_tracking_max_file_bytes(raw: object, field_name: str) -> int:
    return _require_positive_int(raw, field_name)


def _parse_tracking_hash_algorithm(raw: object, field_name: str) -> str:
    return _require_choice(raw, field_name, _ALLOWED_TRACKING_HASH_ALGORITHMS)


def _make_tracking(
    enabled: bool,
    state_file: str,
    scanner: str,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    max_file_bytes: int,
    hash_algorithm: str,
) -> tuple[bool, str, str, tuple[str, ...], tuple[str, ...], int, str]:
    """Factory for the tracking table row."""
    return (
        enabled,
        state_file,
        scanner,
        include,
        exclude,
        max_file_bytes,
        hash_algorithm,
    )


_TRACKING_TABLE = TableSpec(
    name="tracking",
    fields=(
        FieldSpec("enabled", True, _parse_tracking_enabled),
        FieldSpec("state_file", "source-state.json", _parse_tracking_state_file),
        FieldSpec("scanner", "auto", _parse_tracking_scanner),
        FieldSpec("include", DEFAULT_TRACKING_INCLUDE, _parse_tracking_include),
        FieldSpec("exclude", DEFAULT_TRACKING_EXCLUDE, _parse_tracking_exclude),
        FieldSpec("max_file_bytes", 1_000_000, _parse_tracking_max_file_bytes),
        FieldSpec("hash_algorithm", "sha256", _parse_tracking_hash_algorithm),
    ),
    factory=_make_tracking,
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
    ids_data = _validate_subtable(
        path,
        raw_data.get("ids"),
        _ALLOWED_IDS_KEYS,
        "ids",
    )
    source_data = _validate_subtable(
        path,
        raw_data.get("source"),
        _ALLOWED_SOURCE_KEYS,
        "source",
    )
    arc42_data = _validate_subtable(
        path,
        raw_data.get("arc42"),
        _ALLOWED_ARC42_KEYS,
        "arc42",
    )
    skill_data = _validate_subtable(
        path,
        raw_data.get("skill"),
        _ALLOWED_SKILL_KEYS,
        "skill",
    )
    tracking_data = _validate_subtable(
        path,
        raw_data.get("tracking"),
        _ALLOWED_TRACKING_KEYS,
        "tracking",
    )
    diagrams_data = _validate_subtable(
        path,
        raw_data.get("diagrams"),
        _ALLOWED_DIAGRAM_KEYS,
        "diagrams",
    )
    profiles_top_data = _validate_subtable(
        path,
        raw_data.get("profiles"),
        _ALLOWED_PROFILES_KEYS,
        "profiles",
    )

    config_version = raw_data.get("config_version")
    if isinstance(config_version, bool) or config_version not in {
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
    }:
        raise ConfigError("config_version must be 1, 2, 3, 4, 5, 6, 7, or 8.")

    archledger_dir = raw_data.get("archledger_dir")
    if not isinstance(archledger_dir, str) or not archledger_dir.strip():
        raise ConfigError("archledger_dir must be a non-empty string.")

    project_uuid = raw_data.get("project_uuid")
    if not isinstance(project_uuid, str):
        raise ConfigError("project_uuid must be a string.")

    project_name = raw_data.get("project_name")
    if not isinstance(project_name, str):
        raise ConfigError("project_name must be a string.")

    (
        source_format,
        source_schema_version,
        front_matter,
        section_extension,
        record_extension,
    ) = _parse_source_config(source_data, cast(int, config_version))
    (
        default_output,
        build_default_format,
        output_dir,
        include_draft,
        include_superseded,
        strict,
        keep_intermediate,
        build_converter,
        build_pdf_engine,
        reference_docx,
        build_outputs,
    ) = _parse_build_config(build_data, cast(int, config_version), source_format)
    template_version, language, title, include_help = _parse_arc42_config(arc42_data)
    (
        id_prefix,
        id_width,
        id_segment_mode,
        id_default_segment,
        id_segment_map,
    ) = _parse_ids_config(ids_data)
    skill_installed, skill_path = _parse_skill_config(skill_data)
    (
        tracking_enabled,
        tracking_state_file,
        tracking_scanner,
        tracking_include,
        tracking_exclude,
        tracking_max_file_bytes,
        tracking_hash_algorithm,
    ) = _parse_tracking_config(tracking_data)
    (
        diagram_enabled,
        diagram_renderer,
        diagram_default_type,
        diagram_output_dir,
        diagram_image_format,
        diagram_kroki_url,
    ) = _parse_diagram_config(diagrams_data, build_data)
    profiles_present = "profiles" in raw_data and raw_data["profiles"] is not None
    profiles_config = _parse_profiles_config(
        profiles_top_data,
        raw_data,
        config_version=cast(int, config_version),
        archledger_dir=archledger_dir,
    )

    return ProjectConfig(
        config_version=cast(int, config_version),
        archledger_dir=archledger_dir,
        project_uuid=validate_uuid(project_uuid),
        project_name=normalize_project_name(project_name),
        id_prefix=id_prefix,
        id_width=id_width,
        id_segment_mode=id_segment_mode,
        id_default_segment=id_default_segment,
        id_segment_map=id_segment_map,
        source_format=source_format,
        source_schema_version=source_schema_version,
        front_matter=front_matter.strip().lower(),
        section_extension=section_extension,
        record_extension=record_extension,
        build_default_output=default_output,
        build_default_format=build_default_format,
        build_output_dir=output_dir.strip(),
        build_include_draft=include_draft,
        build_include_superseded=include_superseded,
        build_strict=strict,
        build_keep_intermediate=keep_intermediate,
        build_converter=build_converter,
        build_pdf_engine=build_pdf_engine,
        build_reference_docx=reference_docx,
        build_outputs=build_outputs,
        arc42_template_version=template_version,
        arc42_language=language,
        arc42_title=title,
        arc42_include_help=include_help,
        skill_installed=skill_installed,
        skill_path=skill_path,
        tracking_enabled=tracking_enabled,
        tracking_state_file=tracking_state_file,
        tracking_scanner=tracking_scanner,
        tracking_include=tracking_include,
        tracking_exclude=tracking_exclude,
        tracking_max_file_bytes=tracking_max_file_bytes,
        tracking_hash_algorithm=tracking_hash_algorithm,
        diagram_enabled=diagram_enabled,
        diagram_renderer=diagram_renderer,
        diagram_default_type=diagram_default_type,
        diagram_output_dir=diagram_output_dir,
        diagram_image_format=diagram_image_format,
        diagram_kroki_url=diagram_kroki_url,
        profiles=profiles_config,
        profiles_present=profiles_present,
    )


def _parse_ids_config(
    ids_data: dict[str, object],
) -> tuple[str, int, str, str, dict[str, str]]:
    prefix_value = ids_data.get("prefix", DEFAULT_ID_PREFIX)
    width_value = ids_data.get("width", DEFAULT_ID_WIDTH)
    segment_mode_value = ids_data.get("segment_mode", DEFAULT_ID_SEGMENT_MODE)
    default_segment_value = ids_data.get("default_segment", DEFAULT_ID_SEGMENT)
    segment_map_value = ids_data.get("segment_map")

    if not isinstance(prefix_value, str):
        raise ConfigError("ids.prefix must be a string.")
    try:
        prefix = validate_id_prefix(prefix_value)
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc

    try:
        width = validate_id_width(width_value)  # type: ignore[arg-type]
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc

    if not isinstance(segment_mode_value, str):
        raise ConfigError("ids.segment_mode must be a string.")
    try:
        segment_mode = validate_id_segment_mode(segment_mode_value)
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc

    if not isinstance(default_segment_value, str):
        raise ConfigError("ids.default_segment must be a string.")
    try:
        default_segment = validate_id_segment(default_segment_value)
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc

    segment_map = dict(DEFAULT_ID_SEGMENT_MAP)
    if segment_map_value is not None:
        if not isinstance(segment_map_value, dict):
            raise ConfigError("ids.segment_map must be a TOML table.")
        allowed_segment_keys = set(VALID_RECORD_TYPES) | {
            "section",
            "archive_tombstone",
        }
        unknown_keys = sorted(set(segment_map_value) - allowed_segment_keys)
        if unknown_keys:
            joined = ", ".join(unknown_keys)
            raise ConfigError(
                "ids.segment_map contains unknown record types: " + joined
            )
        for key, value in segment_map_value.items():
            if not isinstance(value, str):
                raise ConfigError(f"ids.segment_map.{key} must be a string.")
            try:
                segment_map[key] = validate_id_segment(value)
            except ValueError as exc:
                raise ConfigError(str(exc)) from exc

    return prefix, width, segment_mode, default_segment, segment_map


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


def _parse_source_config(
    source_data: dict[str, object],
    config_version: int,
) -> tuple[str, int, str, str, str]:
    if config_version >= 4 and "format" not in source_data:
        raise ConfigError(
            f"source.format is required for config_version {config_version}."
        )
    source_format_default = "asciidoc" if config_version == 3 else "markdown"
    source_format_value = source_data.get("format", source_format_default)
    if not isinstance(source_format_value, str):
        raise ConfigError("source.format must be a string.")
    source_format = source_format_value.strip().lower()
    if source_format not in VALID_SOURCE_FORMATS:
        raise ConfigError(
            "source.format must be one of: "
            + ", ".join(sorted(VALID_SOURCE_FORMATS))
            + "."
        )

    front_matter_value = source_data.get("front_matter", "yaml")
    if (
        not isinstance(front_matter_value, str)
        or front_matter_value.strip().lower() != "yaml"
    ):
        raise ConfigError('source.front_matter must be the string "yaml".')

    schema_version_value = source_data.get(
        "schema_version",
        CURRENT_SOURCE_SCHEMA_VERSION,
    )
    if isinstance(schema_version_value, bool) or not isinstance(
        schema_version_value, int
    ):
        raise ConfigError("source.schema_version must be an integer.")

    default_extension = default_extension_for_source_format(source_format)
    section_extension = _normalize_extension(
        source_data.get("section_extension", default_extension),
        "source.section_extension",
    )
    record_extension = _normalize_extension(
        source_data.get("record_extension", default_extension),
        "source.record_extension",
    )
    return (
        source_format,
        schema_version_value,
        front_matter_value.strip().lower(),
        section_extension,
        record_extension,
    )


def _parse_build_config(
    build_data: dict[str, object],
    config_version: int,
    source_format: str,
) -> tuple[
    str,
    str,
    str,
    bool,
    bool,
    bool,
    bool,
    str,
    str,
    str,
    dict[str, dict[str, object]],
]:
    default_output_value = build_data.get("default_output")
    if default_output_value is None:
        default_output = ""
    elif isinstance(default_output_value, str) and default_output_value.strip():
        default_output = default_output_value.strip()
    else:
        raise ConfigError("build.default_output must be a non-empty string.")

    default_format_value = build_data.get("default_format")
    if default_format_value is None:
        inferred_default_format = (
            infer_output_format_from_path(default_output) if default_output else None
        )
        build_default_format = source_format if config_version == 3 else "markdown"
        if inferred_default_format is not None:
            build_default_format = inferred_default_format
    elif isinstance(default_format_value, str):
        build_default_format = default_format_value.strip().lower()
        if build_default_format not in VALID_OUTPUT_FORMATS:
            raise ConfigError(
                "build.default_format must be one of: "
                + ", ".join(sorted(VALID_OUTPUT_FORMATS))
                + "."
            )
    else:
        raise ConfigError("build.default_format must be a string.")

    if not default_output:
        default_output = default_document_filename_for_output_format(
            build_default_format
        )
    inferred_output_format = infer_output_format_from_path(default_output)
    if (
        inferred_output_format is not None
        and inferred_output_format != build_default_format
    ):
        raise ConfigError(
            "build.default_output extension must match build.default_format."
        )

    output_dir = _require_non_empty_string(
        build_data.get("default_output_dir", "build"),
        "build.default_output_dir",
    )
    include_draft = _require_bool(
        build_data.get("include_draft", False),
        "build.include_draft",
    )
    include_superseded = _require_bool(
        build_data.get("include_superseded", False),
        "build.include_superseded",
    )
    strict = _require_bool(build_data.get("strict", False), "build.strict")
    keep_intermediate = _require_bool(
        build_data.get("keep_intermediate", False),
        "build.keep_intermediate",
    )
    converter = _require_choice(
        build_data.get("converter", "auto"),
        "build.converter",
        _ALLOWED_BUILD_CONVERTERS,
    )
    pdf_engine = _require_optional_string(
        build_data.get("pdf_engine", ""),
        "build.pdf_engine",
    )
    reference_docx = build_data.get("reference_docx", "")
    if not isinstance(reference_docx, str):
        raise ConfigError("build.reference_docx must be a string.")

    outputs_value = build_data.get("outputs", {})
    if not isinstance(outputs_value, dict):
        raise ConfigError("build.outputs must be a TOML table.")
    build_outputs = _normalize_build_outputs(outputs_value)
    return (
        default_output,
        build_default_format,
        output_dir,
        include_draft,
        include_superseded,
        strict,
        keep_intermediate,
        converter,
        pdf_engine,
        reference_docx,
        build_outputs,
    )


def _parse_arc42_config(
    arc42_data: dict[str, object],
) -> tuple[str, str, str, bool]:
    template_version = _require_non_empty_string(
        arc42_data.get("template_version", "9.0-EN"),
        "arc42.template_version",
    )
    language = _require_non_empty_string(
        arc42_data.get("language", "en"),
        "arc42.language",
    )
    title = _require_non_empty_string(
        arc42_data.get("title", "Architecture Documentation"),
        "arc42.title",
    )
    include_help = _require_bool(
        arc42_data.get("include_help", False),
        "arc42.include_help",
    )
    return template_version, language, title, include_help


def _parse_skill_config(skill_data: dict[str, object]) -> tuple[bool, str]:
    skill_installed = _require_bool(
        skill_data.get("installed", False),
        "skill.installed",
    )
    skill_path = _require_non_empty_string(
        skill_data.get("path", "skills/archledger/SKILL.md"),
        "skill.path",
    )
    return skill_installed, skill_path


def _parse_profiles_config(
    profiles_data: dict[str, object],
    raw_data: dict[str, object],
    *,
    config_version: int,
    archledger_dir: str,
) -> ProjectProfilesConfig:
    """Parse the optional [profiles] table.

    For legacy projects (config_version < 8 with no [profiles] table),
    returns arc42-only defaults with the legacy sections_dir location so
    existing on-disk layouts keep working.
    """
    has_profiles_table = bool(profiles_data)
    if not has_profiles_table:
        # Legacy project: keep sections at the old <archledger_dir>/sections location.
        legacy_sections_dir = archledger_dir.rstrip("/") + "/sections"
        return ProjectProfilesConfig(
            profiles=ProfilesConfig(enabled=("arc42",), default="arc42"),
            arc42=Arc42ProfileConfig(sections_dir=legacy_sections_dir),
            sdd=SddProfileConfig(),
        )

    enabled_raw = profiles_data.get("enabled", ["arc42"])
    if not isinstance(enabled_raw, (list, tuple)):
        raise ConfigError("profiles.enabled must be a list of strings.")
    enabled_list: list[str] = []
    for item in enabled_raw:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError("profiles.enabled must contain only non-empty strings.")
        enabled_list.append(item.strip())
    enabled = tuple(dict.fromkeys(enabled_list))
    unknown_enabled = sorted(set(enabled) - VALID_PROFILES)
    if unknown_enabled:
        raise ConfigError(
            "profiles.enabled contains unknown profiles: " + ", ".join(unknown_enabled)
        )
    if not enabled:
        raise ConfigError("profiles.enabled must contain at least one profile.")

    default_raw = profiles_data.get("default", enabled[0])
    if not isinstance(default_raw, str) or not default_raw.strip():
        raise ConfigError("profiles.default must be a non-empty string.")
    default_profile = default_raw.strip()
    if default_profile not in enabled:
        raise ConfigError(
            f"profiles.default ({default_profile}) must be listed in profiles.enabled."
        )

    arc42_sub = _extract_subtable(
        raw_data, "profiles.arc42", _ALLOWED_PROFILES_ARC42_KEYS
    )
    sdd_sub = _extract_subtable(raw_data, "profiles.sdd", _ALLOWED_PROFILES_SDD_KEYS)

    arc42_cfg = _parse_arc42_profile(arc42_sub)
    sdd_cfg = _parse_sdd_profile(sdd_sub)

    # Validate sections_dir stays inside the archledger directory.
    _validate_profile_sections_dir(arc42_cfg.sections_dir, archledger_dir)

    return ProjectProfilesConfig(
        profiles=ProfilesConfig(enabled=enabled, default=default_profile),
        arc42=arc42_cfg,
        sdd=sdd_cfg,
    )


def _extract_subtable(
    raw_data: dict[str, object], dotted: str, allowed_keys: set[str]
) -> dict[str, object]:
    """Pull a dotted subtable (profiles.arc42) out of raw TOML data."""
    parts = dotted.split(".")
    current: object = raw_data
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return {}
        current = current[part]
    if current is None:
        return {}
    if not isinstance(current, dict):
        raise ConfigError(f"{dotted} must be a TOML table.")
    unknown = sorted(set(current) - allowed_keys)
    if unknown:
        raise ConfigError(f"Unknown keys in {dotted}: " + ", ".join(unknown))
    return dict(current)


def _parse_arc42_profile(data: dict[str, object]) -> Arc42ProfileConfig:
    kind = _require_choice(
        data.get("kind", "documentation"), "profiles.arc42.kind", VALID_PROFILE_KINDS
    )
    template = _require_non_empty_string(
        data.get("template", "arc42"), "profiles.arc42.template"
    )
    sections_dir = _require_non_empty_string(
        data.get("sections_dir", DEFAULT_ARC42_SECTIONS_DIR),
        "profiles.arc42.sections_dir",
    )
    build_template = _require_non_empty_string(
        data.get("build_template", "arc42_document"),
        "profiles.arc42.build_template",
    )
    include_help = _require_bool(
        data.get("include_help", False), "profiles.arc42.include_help"
    )
    return Arc42ProfileConfig(
        kind=kind,
        template=template,
        sections_dir=sections_dir,
        build_template=build_template,
        include_help=include_help,
    )


def _parse_sdd_profile(data: dict[str, object]) -> SddProfileConfig:
    kind = _require_choice(
        data.get("kind", "contract"), "profiles.sdd.kind", VALID_PROFILE_KINDS
    )
    require_acceptance_criteria = _require_bool(
        data.get("require_acceptance_criteria", True),
        "profiles.sdd.require_acceptance_criteria",
    )
    require_implementation_refs = _require_bool(
        data.get("require_implementation_refs", True),
        "profiles.sdd.require_implementation_refs",
    )
    require_test_refs = _require_bool(
        data.get("require_test_refs", True), "profiles.sdd.require_test_refs"
    )
    return SddProfileConfig(
        kind=kind,
        require_acceptance_criteria=require_acceptance_criteria,
        require_implementation_refs=require_implementation_refs,
        require_test_refs=require_test_refs,
    )


def _validate_profile_sections_dir(sections_dir: str, archledger_dir: str) -> None:
    """Validate the arc42 profile sections_dir path syntax.

    Containment against archledger_dir is enforced later by the path resolver.
    """
    from pathlib import Path

    candidate = Path(sections_dir)
    if candidate.is_absolute():
        raise ConfigError("profiles.arc42.sections_dir must be relative.")
    if "\\" in sections_dir:
        raise ConfigError("profiles.arc42.sections_dir must use POSIX separators.")
    if ".." in candidate.parts:
        raise ConfigError("profiles.arc42.sections_dir must not contain '..'.")


def _parse_tracking_config(
    tracking_data: dict[str, object],
) -> tuple[bool, str, str, tuple[str, ...], tuple[str, ...], int, str]:
    parsed = parse_table_from_spec(tracking_data, _TRACKING_TABLE)
    return cast(
        tuple[bool, str, str, tuple[str, ...], tuple[str, ...], int, str],
        _TRACKING_TABLE.factory(**parsed),
    )


def _parse_diagram_config(
    diagrams_data: dict[str, object],
    build_data: dict[str, object],
) -> tuple[bool, str, str, str, str, str]:
    build_diagrams_raw = build_data.get("diagrams")
    if build_diagrams_raw is None:
        build_diagrams_data: dict[str, object] = {}
    elif isinstance(build_diagrams_raw, dict):
        unknown_keys = sorted(set(build_diagrams_raw) - _ALLOWED_DIAGRAM_KEYS)
        if unknown_keys:
            joined = ", ".join(unknown_keys)
            raise ConfigError(f"Unknown keys in build.diagrams: {joined}")
        build_diagrams_data = dict(build_diagrams_raw)
    else:
        raise ConfigError("build.diagrams must be a TOML table.")

    effective_data = diagrams_data if diagrams_data else build_diagrams_data
    enabled = _require_bool(effective_data.get("enabled", False), "diagrams.enabled")
    renderer = _require_choice(
        effective_data.get("renderer", "pass-through"),
        "diagrams.renderer",
        _ALLOWED_DIAGRAM_RENDERERS,
    )
    default_type = _require_choice(
        effective_data.get("default_type", "text"),
        "diagrams.default_type",
        _ALLOWED_DIAGRAM_TYPES,
    )
    output_dir = _require_non_empty_string(
        effective_data.get("output_dir", "diagrams"),
        "diagrams.output_dir",
    )
    image_format = _require_choice(
        effective_data.get("image_format", "svg"),
        "diagrams.image_format",
        _ALLOWED_DIAGRAM_IMAGE_FORMATS,
    )
    kroki_url = _require_optional_string(
        effective_data.get("kroki_url", ""),
        "diagrams.kroki_url",
    )
    return enabled, renderer, default_type, output_dir, image_format, kroki_url


def _normalize_extension(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} must be a non-empty string.")
    normalized = value.strip().lower()
    if not normalized.startswith(".") or len(normalized) == 1:
        raise ConfigError(f"{field_name} must start with a file extension dot.")
    return normalized


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{field_name} must be a boolean.")
    return value


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _require_optional_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{field_name} must be a string.")
    return value.strip()


def _require_choice(value: object, field_name: str, allowed: frozenset[str]) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{field_name} must be a string.")
    normalized = value.strip().lower()
    if normalized not in allowed:
        raise ConfigError(
            f"{field_name} must be one of: " + ", ".join(sorted(allowed)) + "."
        )
    return normalized


def _require_string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ConfigError(f"{field_name} must be a list of strings.")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError(f"{field_name} must contain only non-empty strings.")
        items.append(item.strip())
    return tuple(items)


def _require_positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigError(f"{field_name} must be a positive integer.")
    return value


def _normalize_build_outputs(value: dict[str, object]) -> dict[str, dict[str, object]]:
    normalized: dict[str, dict[str, object]] = {}
    for output_name, raw_config in value.items():
        normalized_name = str(output_name).strip().lower()
        if normalized_name not in VALID_OUTPUT_FORMATS:
            raise ConfigError(
                f"build.outputs.{output_name} is not a supported output format."
            )
        if not isinstance(raw_config, dict):
            raise ConfigError(f"build.outputs.{output_name} must be a TOML table.")
        unknown_keys = sorted(set(raw_config) - _ALLOWED_BUILD_OUTPUT_KEYS)
        if unknown_keys:
            raise ConfigError(
                f"Unknown keys in build.outputs.{output_name}: "
                + ", ".join(unknown_keys)
            )
        output_config: dict[str, object] = {}
        enabled = raw_config.get("enabled")
        if enabled is not None:
            output_config["enabled"] = _require_bool(
                enabled,
                f"build.outputs.{normalized_name}.enabled",
            )
        tool = raw_config.get("tool")
        if tool is not None:
            output_config["tool"] = _require_choice(
                tool,
                f"build.outputs.{normalized_name}.tool",
                _ALLOWED_BUILD_CONVERTERS,
            )
        pdf_engine = raw_config.get("pdf_engine")
        if pdf_engine is not None:
            output_config["pdf_engine"] = _require_optional_string(
                pdf_engine,
                f"build.outputs.{normalized_name}.pdf_engine",
            )
        reference_docx = raw_config.get("reference_docx")
        if reference_docx is not None:
            output_config["reference_docx"] = _require_optional_string(
                reference_docx,
                f"build.outputs.{normalized_name}.reference_docx",
            )
        normalized[normalized_name] = output_config
    return normalized
