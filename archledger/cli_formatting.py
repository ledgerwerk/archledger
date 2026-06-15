from __future__ import annotations

from typing import cast

import yaml


def format_init_message(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            f"Initialized archledger in {payload['workspace_root']}",
            f"Config: {payload['config_path']}",
            f"State: {payload['archledger_dir']}",
        ]
    )


def format_status_message(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            f"Project: {payload['project_name']}",
            f"Workspace: {payload['workspace_root']}",
            f"Config: {payload['config_path']}",
            f"State: {payload['archledger_dir']}",
            f"Sections: {payload['sections_count']}",
            f"Record directories: {payload['record_directories_count']}",
        ]
    )


def format_paths_message(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            f"Workspace: {payload['workspace_root']}",
            f"Config: {payload['config_path']}",
            f"State: {payload['archledger_dir']}",
            f"Sections: {payload['sections_dir']}",
            f"Records: {payload['records_dir']}",
            f"Build: {payload['build_dir']}",
            f"Storage metadata: {payload['storage_meta_path']}",
            f"Source state: {payload['source_state_path']}",
        ]
    )


def format_schema_message(payload: dict[str, object]) -> str:
    record_types = payload.get("record_types")
    statuses = payload.get("statuses")
    sections = payload.get("sections")
    source_formats = payload.get("source_formats")
    output_formats = payload.get("output_formats")
    if (
        not isinstance(record_types, list)
        or not isinstance(statuses, list)
        or not isinstance(sections, list)
        or not isinstance(source_formats, list)
        or not isinstance(output_formats, list)
    ):
        raise RuntimeError("Schema payload was malformed.")
    return "\n".join(
        [
            f"Record types: {len(record_types)}",
            f"Statuses: {', '.join(statuses)}",
            f"Sections: {len(sections)}",
            f"Source formats: {', '.join(source_formats)}",
            f"Output formats: {', '.join(output_formats)}",
        ]
    )


def format_new_message(payload: dict[str, object]) -> str:
    return f"Created {payload['id']}: {payload['path']}"


def format_seed_message(payload: dict[str, object]) -> str:
    records = payload.get("records")
    if not isinstance(records, list):
        raise RuntimeError("Seed payload was malformed.")
    return f"Seeded {payload['preset']} with {len(records)} record(s)."


def format_list_message(payload: dict[str, object]) -> str:
    records = payload["records"]
    if not isinstance(records, list) or not records:
        return "No records found."
    lines = []
    for item in records:
        if not isinstance(item, dict):
            continue
        lines.append(f"{item['id']}  {item['type']}  {item['status']}  {item['title']}")
    return "\n".join(lines)


def format_show_message(payload: dict[str, object]) -> str:
    metadata = payload["metadata"]
    body = payload["body"]
    if not isinstance(metadata, dict) or not isinstance(body, str):
        raise RuntimeError("Show payload was malformed.")
    yaml_text = yaml.safe_dump(metadata, sort_keys=False).rstrip()
    document = f"Path: {payload['path']}\n---\n{yaml_text}\n---"
    if body:
        document = f"{document}\n\n{body.rstrip()}"
    return document


def format_read_message(payload: dict[str, object]) -> str:
    records = payload.get("records")
    project = payload.get("project")
    if not isinstance(records, list) or not isinstance(project, dict):
        raise RuntimeError("Read payload was malformed.")
    return (
        f"Read {len(records)} source fragment(s) from "
        f"{project.get('name', 'unknown-project')}."
    )


def format_check_message(payload: dict[str, object]) -> str:
    error_messages = payload["errors"]
    warning_messages = payload["warnings"]
    if not isinstance(error_messages, list) or not isinstance(warning_messages, list):
        raise RuntimeError("Check payload was malformed.")
    lines = [
        (
            "Check completed: "
            f"{len(error_messages)} error(s), "
            f"{len(warning_messages)} warning(s)"
        ),
    ]
    for entry in error_messages:
        if isinstance(entry, dict):
            lines.append(f"error: {entry['message']}")
    for entry in warning_messages:
        if isinstance(entry, dict):
            lines.append(f"warning: {entry['message']}")
    return "\n".join(lines)


def format_archive_message(payload: dict[str, object]) -> str:
    if payload.get("already_archived"):
        return f"Already archived {payload['id']}: {payload['to']}"
    return f"Archived {payload['id']}: {payload['from']} -> {payload['to']}"


def format_doctor_message(payload: dict[str, object]) -> str:
    errors = payload.get("errors", [])
    warnings = payload.get("warnings", [])
    repairs = payload.get("repairs", [])
    if (
        not isinstance(errors, list)
        or not isinstance(warnings, list)
        or not isinstance(repairs, list)
    ):
        raise RuntimeError("Doctor payload was malformed.")
    lines = [
        (
            f"Doctor completed: {len(errors)} error(s), "
            f"{len(warnings)} warning(s), {len(repairs)} repair(s)"
        )
    ]
    for entry in errors:
        if isinstance(entry, dict):
            lines.append(f"error: {entry['message']}")
    for entry in warnings:
        if isinstance(entry, dict):
            lines.append(f"warning: {entry['message']}")
    for entry in repairs:
        if isinstance(entry, dict):
            lines.append(f"repair: {entry['message']}")
    return "\n".join(lines)


def format_snapshot_message(payload: dict[str, object]) -> str:
    return (
        f"Snapshot saved to {payload['source_state_path']} "
        f"({payload['file_count']} file(s), scanner: {payload['scanner_used']})."
    )


def format_changed_message(payload: dict[str, object]) -> str:
    baseline = payload.get("baseline")
    changes = payload.get("changes")
    impact = payload.get("impact")
    if (
        not isinstance(baseline, dict)
        or not isinstance(changes, dict)
        or not isinstance(impact, dict)
    ):
        raise RuntimeError("Changed payload was malformed.")
    if baseline.get("exists") is False:
        lines = ["No source baseline found. Run: archledger source snapshot"]
        for path in changes.get("unbaselined_files", []):
            lines.append(f"- unbaselined: {path}")
        return "\n".join(lines)

    lines = [f"Changed since baseline version {baseline.get('version', 'unknown')}:"]
    for label in ("modified", "added", "deleted"):
        entries = changes.get(label, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict):
                lines.append(f"- {label}: {entry['path']}")
    rename_entries = changes.get("possible_renames", [])
    if isinstance(rename_entries, list):
        for entry in rename_entries:
            if isinstance(entry, dict):
                lines.append(
                    f"- possible rename: {entry['old_path']} -> {entry['new_path']}"
                )
    sections = impact.get("sections", [])
    if isinstance(sections, list) and sections:
        lines.append("")
        lines.append("Impacted archledger sections:")
        for section in sections:
            lines.append(f"- {section}")
    records = impact.get("records", [])
    if isinstance(records, list) and records:
        lines.append("")
        lines.append("Impacted records:")
        for record in records:
            if isinstance(record, dict):
                lines.append(f"- {record['id']} {record['title']}")
    unlinked = impact.get("unlinked_changed_files", [])
    if isinstance(unlinked, list) and unlinked:
        lines.append("")
        lines.append("Unlinked changed files:")
        for path in unlinked:
            lines.append(f"- {path}")
    return "\n".join(lines)


def format_build_message(payload: dict[str, object]) -> str:
    outputs = payload.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise RuntimeError("Build payload was malformed.")
    if len(outputs) == 1 and isinstance(outputs[0], dict):
        return f"Built {outputs[0]['format']}: {outputs[0]['output_path']}"

    lines = ["Built outputs:"]
    for item in outputs:
        if isinstance(item, dict):
            lines.append(f"{item['format']}: {item['output_path']}")
    return "\n".join(lines)


def format_convert_sources_message(payload: dict[str, object]) -> str:
    converted = payload.get("converted")
    warnings = payload.get("warnings")
    if not isinstance(converted, list) or not isinstance(warnings, list):
        raise RuntimeError("convert-sources payload was malformed.")
    action = "Converted" if payload.get("write") else "Planned"
    lines = [
        f"{action} {len(converted)} source file(s) to {payload['target_format']}.",
    ]
    if not payload.get("write"):
        lines.append("Re-run with --apply to apply the migration.")
    for warning in warnings:
        lines.append(f"warning: {warning}")
    return "\n".join(lines)


def format_renumber_message(payload: dict[str, object]) -> str:
    old_format = payload.get("old_format")
    new_format = payload.get("new_format")
    if not isinstance(old_format, dict) or not isinstance(new_format, dict):
        raise RuntimeError("renumber payload was malformed.")
    action = "Renumbered" if payload.get("apply") else "Planned renumbering"
    lines = [
        (
            f"{action}: "
            f"{old_format['prefix']}/{old_format['width']}/"
            f"{old_format.get('segment_mode', 'none')}"
            f" -> {new_format['prefix']}/{new_format['width']}/"
            f"{new_format.get('segment_mode', 'none')}"
        ),
        f"Files to rename: {payload['renamed_count']}",
        f"Files to rewrite: {payload['rewritten_count']}",
    ]
    quarantined = payload.get("quarantined_generated_tombstones_count", 0)
    if isinstance(quarantined, int) and quarantined > 0:
        quarantined_list = cast(
            "list[object]", payload.get("quarantined_generated_tombstones", [])
        )
        lines.append(f"Generated tombstones quarantined: {quarantined}")
        for q in quarantined_list:
            if isinstance(q, dict):
                lines.append(f"  {q.get('path')} -> {q.get('quarantine_path')}")
    if not payload.get("apply"):
        lines.append("Re-run with --apply to apply the renumbering.")
    return "\n".join(lines)


def format_profile_list_message(payload: dict[str, object]) -> str:
    enabled = payload.get("enabled", [])
    default = payload.get("default", "arc42")
    available = payload.get("available", [])
    enabled_str = ", ".join(enabled) if isinstance(enabled, list) else str(enabled)
    available_str = (
        ", ".join(available) if isinstance(available, list) else str(available)
    )
    return "\n".join(
        [
            f"Default profile: {default}",
            f"Enabled: {enabled_str}",
            f"Available to enable: {available_str or '(none)'}",
        ]
    )


def format_profile_migration_message(payload: dict[str, object]) -> str:
    profile = payload.get("profile", "")
    write = payload.get("write", False)
    changed = payload.get("changed", False)
    steps = payload.get("steps", [])
    action = "Applied" if write else "Planned"
    lines = [f"{action} profile '{profile}' migration (changed: {bool(changed)})."]
    if not write:
        lines.append("Re-run with --write to apply.")
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict):
                lines.append(f"- {step.get('action')}: {step.get('message')}")
    return "\n".join(lines)
