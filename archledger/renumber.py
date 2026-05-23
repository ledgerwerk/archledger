from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from pathlib import Path
from re import Match
from uuid import uuid4

from archledger.errors import ValidationError
from archledger.id_segments import id_segment_for_metadata
from archledger.ids import LedgerIdFormat
from archledger.model import SOURCE_FORMAT_EXTENSIONS
from archledger.storage.common import ensure_dir, read_text, write_text_atomic
from archledger.storage.frontmatter import iter_source_files, read_front_matter_document
from archledger.storage.meta import (
    next_number_floor,
    read_storage_meta,
    write_storage_meta,
)
from archledger.storage.paths import ProjectPaths
from archledger.storage.project_config import ProjectConfig, render_project_config


@dataclass(frozen=True, slots=True)
class RenumberedPath:
    old_id: str
    new_id: str
    old_path: Path
    new_path: Path


@dataclass(frozen=True, slots=True)
class RewrittenFile:
    path: Path
    replacement_count: int


@dataclass(frozen=True, slots=True)
class RenumberResult:
    apply: bool
    old_prefix: str
    old_width: int
    old_segment_mode: str
    new_prefix: str
    new_width: int
    new_segment_mode: str
    renamed: tuple[RenumberedPath, ...]
    rewritten: tuple[RewrittenFile, ...]
    config_path: Path
    storage_next_number_before: int
    storage_next_number_after: int


@dataclass(frozen=True, slots=True)
class _RewritePreview:
    path: Path
    replacement_count: int
    new_text: str


@dataclass(frozen=True, slots=True)
class NumberedPathForRenumber:
    path: Path
    old_id: str
    number: int
    metadata: dict[str, object]


def renumber_project(
    paths: ProjectPaths,
    config: ProjectConfig,
    *,
    new_prefix: str | None = None,
    new_width: int | None = None,
    new_segment_mode: str | None = None,
    apply: bool,
) -> RenumberResult:
    old_format = config.id_format
    try:
        new_format = LedgerIdFormat(
            prefix=new_prefix or config.id_prefix,
            width=new_width if new_width is not None else config.id_width,
            segment_mode=new_segment_mode or config.id_segment_mode,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc

    source_extensions = _known_source_extensions(config)
    numbered_paths = _collect_numbered_paths(paths, source_extensions, old_format)
    if not numbered_paths:
        raise ValidationError("No source files match the current ledger ID format.")

    rename_plan, id_mapping = _build_rename_plan(numbered_paths, config, new_format)
    _validate_no_target_collisions(rename_plan)

    rewrite_plan = _build_rewrite_plan(
        paths.archledger_dir,
        source_extensions,
        old_format,
        id_mapping,
    )
    if old_format == new_format and not rename_plan and not rewrite_plan:
        raise ValidationError("New ledger ID format is identical to current format.")

    meta_before = read_storage_meta(paths.storage_meta_path)

    if apply:
        _rewrite_files(rewrite_plan)
        _rename_files(rename_plan)
        new_config = dataclass_replace(
            config,
            id_prefix=new_format.prefix,
            id_width=new_format.width,
            id_segment_mode=new_format.segment_mode,
            config_version=max(config.config_version, 7),
        )
        write_text_atomic(paths.config_path, render_project_config(new_config))
        next_after = next_number_floor(
            paths.archledger_dir,
            meta_before.next_number,
            source_extensions=source_extensions,
            id_format=new_format,
        )
        write_storage_meta(
            paths.storage_meta_path,
            dataclass_replace(meta_before, next_number=next_after),
        )
    else:
        next_after = meta_before.next_number

    return RenumberResult(
        apply=apply,
        old_prefix=old_format.prefix,
        old_width=old_format.width,
        old_segment_mode=old_format.segment_mode,
        new_prefix=new_format.prefix,
        new_width=new_format.width,
        new_segment_mode=new_format.segment_mode,
        renamed=rename_plan,
        rewritten=tuple(
            RewrittenFile(path=item.path, replacement_count=item.replacement_count)
            for item in rewrite_plan
        ),
        config_path=paths.config_path,
        storage_next_number_before=meta_before.next_number,
        storage_next_number_after=next_after,
    )


def _known_source_extensions(config: ProjectConfig) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                *SOURCE_FORMAT_EXTENSIONS.values(),
                config.section_extension,
                config.record_extension,
            }
        )
    )


def _collect_numbered_paths(
    paths: ProjectPaths,
    source_extensions: tuple[str, ...],
    old_format: LedgerIdFormat,
) -> tuple[NumberedPathForRenumber, ...]:
    collected: list[NumberedPathForRenumber] = []
    for root in (paths.sections_dir, paths.records_dir, paths.archive_dir):
        for path in iter_source_files(root, source_extensions):
            try:
                number = old_format.parse(path.stem)
            except ValueError:
                continue
            metadata, _body = read_front_matter_document(path)
            collected.append(
                NumberedPathForRenumber(
                    path=path,
                    old_id=path.stem,
                    number=number,
                    metadata=metadata,
                )
            )
    return tuple(sorted(collected, key=lambda item: str(item.path)))


def _build_rename_plan(
    numbered_paths: tuple[NumberedPathForRenumber, ...],
    config: ProjectConfig,
    new_format: LedgerIdFormat,
) -> tuple[tuple[RenumberedPath, ...], dict[str, str]]:
    items: list[RenumberedPath] = []
    id_mapping: dict[str, str] = {}
    seen_old_ids: set[str] = set()

    for item in numbered_paths:
        old_id = item.old_id
        if old_id in seen_old_ids:
            raise ValidationError(f"Duplicate ledger ID found in filesystem: {old_id}")
        seen_old_ids.add(old_id)

        segment = id_segment_for_metadata(
            item.metadata,
            default_segment=config.id_default_segment,
            segment_map=config.id_segment_map,
        )
        new_id = new_format.format(item.number, segment=segment)
        id_mapping[old_id] = new_id

        new_path = item.path.with_name(f"{new_id}{item.path.suffix}")
        if new_path != item.path:
            items.append(
                RenumberedPath(
                    old_id=old_id,
                    new_id=new_id,
                    old_path=item.path,
                    new_path=new_path,
                )
            )

    return tuple(items), id_mapping


def _validate_no_target_collisions(rename_plan: tuple[RenumberedPath, ...]) -> None:
    if not rename_plan:
        return

    old_paths = {item.old_path for item in rename_plan}
    target_paths = [item.new_path for item in rename_plan]
    if len(target_paths) != len(set(target_paths)):
        raise ValidationError("Renumbering target collision: duplicate target paths.")

    for target in target_paths:
        if target.exists() and target not in old_paths:
            raise ValidationError(
                f"Renumbering would overwrite existing file: {target}"
            )


def _build_rewrite_plan(
    archledger_dir: Path,
    source_extensions: tuple[str, ...],
    old_format: LedgerIdFormat,
    id_mapping: dict[str, str],
) -> tuple[_RewritePreview, ...]:
    reference_pattern = old_format.reference_pattern()
    rewrites: list[_RewritePreview] = []

    for path in iter_source_files(archledger_dir, source_extensions):
        source_text = read_text(path)
        replacement_count = 0

        def replace_match(match: Match[str], _path: Path = path) -> str:
            nonlocal replacement_count
            matched = match.group(0)
            mapped = id_mapping.get(matched)
            if mapped is None:
                raise ValidationError(
                    "Found ledger reference that does not map to an existing source "
                    f"file: {matched} in {_path}"
                )
            replacement_count += 1
            return mapped

        updated_text = reference_pattern.sub(replace_match, source_text)
        if replacement_count > 0:
            rewrites.append(
                _RewritePreview(
                    path=path,
                    replacement_count=replacement_count,
                    new_text=updated_text,
                )
            )

    return tuple(rewrites)


def _rewrite_files(rewrite_plan: Iterable[_RewritePreview]) -> None:
    for item in rewrite_plan:
        write_text_atomic(item.path, item.new_text)


def _rename_files(rename_plan: tuple[RenumberedPath, ...]) -> None:
    if not rename_plan:
        return

    temp_paths: list[tuple[Path, Path]] = []
    token = uuid4().hex
    for index, item in enumerate(rename_plan, start=1):
        ensure_dir(item.old_path.parent)
        temp_path = item.old_path.with_name(
            f".{item.old_path.name}.renumber.{token}.{index}.tmp"
        )
        if temp_path.exists():
            raise ValidationError(f"Temporary rename path already exists: {temp_path}")
        item.old_path.rename(temp_path)
        temp_paths.append((temp_path, item.new_path))

    for temp_path, final_path in temp_paths:
        ensure_dir(final_path.parent)
        temp_path.rename(final_path)
