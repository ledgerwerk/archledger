from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from pathlib import Path

from ledgercore.errors import IdFormatError
from ledgercore.refs import parse_local_ref, parse_resource_ref

from archledger.errors import ValidationError
from archledger.ids import format_local_id, global_ref_for
from archledger.model import known_source_extensions
from archledger.renumber import RewrittenFile
from archledger.storage.frontmatter import iter_source_files, read_front_matter_document
from archledger.storage.frontmatter import (
    write_front_matter_document as write_frontmatter,
)
from archledger.storage.meta import (
    next_number_floor,
    read_storage_meta,
    write_storage_meta,
)
from archledger.storage.paths import ProjectPaths
from archledger.storage.project_config import ProjectConfig, render_project_config

LEGACY_UNSEGMENTED_RE = re.compile(r"^[a-z][a-z0-9]*_(\d+)$")


@dataclass(frozen=True, slots=True)
class MigratedIdentityPath:
    old_id: str
    new_id: str
    old_ref: str
    new_ref: str
    old_path: Path
    new_path: Path


@dataclass(frozen=True, slots=True)
class IdentityMigrationResult:
    apply: bool
    ledger_code: str
    migrated: tuple[MigratedIdentityPath, ...]
    rewritten: tuple[RewrittenFile, ...]
    config_path: Path
    storage_next_number_before: int
    storage_next_number_after: int


def migrate_identity(
    paths: ProjectPaths,
    config: ProjectConfig,
    *,
    apply: bool,
) -> IdentityMigrationResult:
    source_extensions = known_source_extensions(config)
    numbered = _collect(paths, config, source_extensions)
    id_mapping = {old_id: new_id for old_id, new_id, _ in numbered if old_id != new_id}
    rewrite_plan = _build_rewrite_plan(
        paths.archledger_dir, source_extensions, id_mapping
    )
    meta_before = read_storage_meta(paths.storage_meta_path)

    if apply:
        # Rewrite cross-record references before renaming any source file.
        #
        # The rewrite plan is built from the pre-migration path set.  Applying it
        # after renames recreates the old filenames with rewritten front matter,
        # leaving duplicate source files such as both ``al_content_0001.md`` and
        # ``content-0001.md``.  Apply global text rewrites first, then perform the
        # canonical metadata/body write, then rename the source files.
        for item in rewrite_plan:
            item.path.write_text(item.new_text, encoding="utf-8")
        for old_id, new_id, path in numbered:
            metadata, body = read_front_matter_document(path)
            metadata = _rewrite_metadata(metadata, old_id, new_id, id_mapping)
            rewritten_body = _rewrite_text(body, id_mapping)
            write_frontmatter(path, metadata, rewritten_body)
        for old_id, new_id, path in numbered:
            if old_id == new_id:
                continue
            path.rename(path.with_name(f"{new_id}{path.suffix}"))

        new_config = dataclass_replace(
            config,
            config_version=max(config.config_version, 9),
            id_segment_mode="type",
            id_default_segment=config.id_default_kind,
            id_segment_map=dict(config.id_kind_map),
        )
        paths.config_path.write_text(
            render_project_config(new_config), encoding="utf-8"
        )
        next_after = next_number_floor(
            paths.archledger_dir,
            meta_before.next_number,
            source_extensions=source_extensions,
        )
        write_storage_meta(
            paths.storage_meta_path,
            dataclass_replace(meta_before, next_number=next_after),
        )
    else:
        next_after = meta_before.next_number

    migrated = tuple(
        MigratedIdentityPath(
            old_id=old_id,
            new_id=new_id,
            old_ref=global_ref_for(old_id, config.ledger_code)
            if _is_local(old_id, config.id_width)
            else f"{config.ledger_code}:{old_id}",
            new_ref=global_ref_for(new_id, config.ledger_code),
            old_path=path,
            new_path=path.with_name(f"{new_id}{path.suffix}"),
        )
        for old_id, new_id, path in numbered
        if old_id != new_id
    )
    rewritten = tuple(
        RewrittenFile(path=item.path, replacement_count=item.replacement_count)
        for item in rewrite_plan
    )
    return IdentityMigrationResult(
        apply=apply,
        ledger_code=config.ledger_code,
        migrated=migrated,
        rewritten=rewritten,
        config_path=paths.config_path,
        storage_next_number_before=meta_before.next_number,
        storage_next_number_after=next_after,
    )


def _collect(
    paths: ProjectPaths,
    config: ProjectConfig,
    source_extensions: tuple[str, ...],
) -> list[tuple[str, str, Path]]:
    seen_new: dict[str, Path] = {}
    rows: list[tuple[str, str, Path]] = []
    for root in (paths.sections_dir, paths.records_dir, paths.archive_dir):
        for path in iter_source_files(root, source_extensions):
            metadata, _body = read_front_matter_document(path)
            raw_id = str(metadata.get("id", path.stem)).strip()
            record_type = str(metadata.get("type", "")).strip()
            kind = str(metadata.get("kind", "")).strip() or config.id_kind_map.get(
                record_type, config.id_default_kind
            )
            number = _extract_number(raw_id, metadata, config, kind)
            new_id = format_local_id(kind, number, width=config.id_width)
            if new_id in seen_new and seen_new[new_id] != path:
                raise ValidationError(
                    f"Identity migration collision for target ID {new_id}."
                )
            seen_new[new_id] = path
            rows.append((raw_id, new_id, path))
    return rows


def _extract_number(
    raw_id: str,
    metadata: dict[str, object],
    config: ProjectConfig,
    kind: str,
) -> int:
    try:
        return parse_local_ref(raw_id, width=config.id_width).number
    except IdFormatError:
        pass
    try:
        return parse_resource_ref(
            raw_id,
            default_ledger=config.ledger_code,
            width=config.id_width,
            allow_legacy_alias=True,
        ).number
    except IdFormatError:
        pass
    match = LEGACY_UNSEGMENTED_RE.fullmatch(raw_id)
    if match is not None:
        return int(match.group(1))
    raise ValidationError(
        f"Cannot derive number for legacy ID {raw_id!r} (kind={kind!r})."
    )


@dataclass(frozen=True, slots=True)
class _RewritePlan:
    path: Path
    replacement_count: int
    new_text: str


def _build_rewrite_plan(
    archledger_dir: Path,
    source_extensions: tuple[str, ...],
    id_mapping: dict[str, str],
) -> tuple[_RewritePlan, ...]:
    if not id_mapping:
        return ()
    rewrites: list[_RewritePlan] = []
    token_re = re.compile(
        r"(?<![A-Za-z0-9:_-])("
        + "|".join(re.escape(k) for k in sorted(id_mapping, key=len, reverse=True))
        + r")(?![A-Za-z0-9:_-])"
    )
    for path in iter_source_files(archledger_dir, source_extensions):
        text = path.read_text(encoding="utf-8")
        count = 0

        def _replace(match: re.Match[str]) -> str:
            nonlocal count
            old = match.group(1)
            new = id_mapping.get(old, old)
            if new != old:
                count += 1
            return new

        updated = token_re.sub(_replace, text)
        if count > 0:
            rewrites.append(
                _RewritePlan(path=path, replacement_count=count, new_text=updated)
            )
    return tuple(rewrites)


def _rewrite_text(text: str, id_mapping: dict[str, str]) -> str:
    if not id_mapping:
        return text
    rewritten = text
    for old, new in sorted(
        id_mapping.items(), key=lambda item: len(item[0]), reverse=True
    ):
        rewritten = re.sub(
            rf"(?<![A-Za-z0-9:_-]){re.escape(old)}(?![A-Za-z0-9:_-])",
            new,
            rewritten,
        )
    return rewritten


def _rewrite_metadata(
    metadata: dict[str, object],
    old_id: str,
    new_id: str,
    id_mapping: dict[str, str],
) -> dict[str, object]:
    rewritten = dict(metadata)
    rewritten["id"] = new_id
    rewritten["kind"] = new_id.split("-", 1)[0]
    if "parent" in rewritten and isinstance(rewritten["parent"], str):
        rewritten["parent"] = id_mapping.get(rewritten["parent"], rewritten["parent"])
    links = rewritten.get("links")
    if isinstance(links, list):
        new_links: list[object] = []
        for item in links:
            if isinstance(item, dict):
                target = item.get("target")
                if isinstance(target, str):
                    item = {**item, "target": id_mapping.get(target, target)}
            new_links.append(item)
        rewritten["links"] = new_links
    if old_id != new_id:
        rewritten.pop("id_segment", None)
    return rewritten


def _is_local(value: str, width: int) -> bool:
    try:
        parse_local_ref(value, width=width)
    except IdFormatError:
        return False
    return True
