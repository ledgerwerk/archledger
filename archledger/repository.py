from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from pathlib import Path
from typing import cast

from jinja2 import Environment, PackageLoader, select_autoescape
from ledgercore.errors import IdFormatError
from ledgercore.refs import normalize_kind as normalize_resource_kind
from ledgercore.refs import parse_local_ref

from archledger import __version__
from archledger.checks import content_warnings
from archledger.errors import StorageError, ValidationError
from archledger.id_format_drift import find_id_format_drift
from archledger.id_segments import identity_kind_for_metadata
from archledger.identity_detection import detect_identity_format_state
from archledger.ids import format_local_id, global_ref_for
from archledger.ledger_sequence import (
    NumberedSourcePath as _NumberedSourcePath,
)
from archledger.ledger_sequence import (
    analyze_ledger_sequence as _analyze_ledger_sequence,
)
from archledger.ledger_sequence import (
    collect_numbered_source_paths as _collect_numbered_source_paths,
)
from archledger.links import normalize_links
from archledger.metadata_version import bump_metadata_version
from archledger.model import (
    CURRENT_SOURCE_SCHEMA_VERSION,
    MAJOR_SECTION_SPECS,
    RECORD_TYPE_TO_DEFAULT_SECTION,
    RECORD_TYPE_TO_DIR,
    RECORD_TYPES,
    REQUIRED_RECORD_FIELDS,
    VALID_BODY_FORMATS,
    ArchitectureRecord,
    SectionSpec,
    is_visible_status,
    known_source_extensions,
    normalize_kind,
    record_sort_key,
    record_template_name_for_source_format,
    section_body_placeholder_for_source_format,
    validate_record,
)
from archledger.record_types import RecordContextInput
from archledger.scopes import normalize_scope
from archledger.source_refs import normalize_source_refs
from archledger.storage.common import ensure_dir, write_text_atomic
from archledger.storage.frontmatter import (
    FrontMatterError,
    iter_source_files,
    read_front_matter_document,
    write_front_matter_document,
)
from archledger.storage.meta import (
    default_storage_meta,
    next_number_floor,
    read_storage_meta,
    write_storage_meta,
)
from archledger.storage.paths import ProjectPaths, is_relative_to
from archledger.storage.project_config import ProjectConfig
from archledger.test_refs import normalize_test_refs


@dataclass(frozen=True, slots=True)
class InitResult:
    workspace_root: Path
    config_path: Path
    archledger_dir: Path
    created_paths: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class StatusResult:
    workspace_root: Path
    config_path: Path
    archledger_dir: Path
    archive_dir: Path
    sections_count: int
    record_directories_count: int
    storage_meta_path: Path
    build_dir: Path


@dataclass(frozen=True, slots=True)
class CheckFinding:
    level: str
    message: str
    path: Path | None = None


@dataclass(frozen=True, slots=True)
class CheckResult:
    errors: tuple[CheckFinding, ...]
    warnings: tuple[CheckFinding, ...]

    def has_failures(self, *, strict: bool) -> bool:
        return bool(self.errors) or (strict and bool(self.warnings))


@dataclass(frozen=True, slots=True)
class ArchiveResult:
    record_id: str
    source_path: Path
    archive_path: Path
    reason: str
    already_archived: bool = False


@dataclass(frozen=True, slots=True)
class DoctorRepair:
    kind: str
    message: str
    path: Path | None = None
    before: int | None = None
    after: int | None = None


@dataclass(frozen=True, slots=True)
class DoctorResult:
    errors: tuple[CheckFinding, ...]
    warnings: tuple[CheckFinding, ...]
    repairs: tuple[DoctorRepair, ...]
    storage_next_number_before: int
    storage_next_number_after: int
    highest_seen: int
    missing_numbers: tuple[int, ...]
    duplicate_numbers: tuple[int, ...]


# Re-export for backward compatibility
NumberedSourcePath = _NumberedSourcePath


class ArchitectureRepository:
    def __init__(self, paths: ProjectPaths, config: ProjectConfig) -> None:
        self.paths = paths
        self.config = config
        self._template_env = Environment(
            loader=PackageLoader("archledger", "templates"),
            autoescape=select_autoescape(
                enabled_extensions=(),
                default_for_string=False,
            ),
            keep_trailing_newline=True,
            trim_blocks=False,
            lstrip_blocks=False,
        )

    def init(self, *, overwrite: bool = False) -> InitResult:
        created_paths: list[Path] = []
        dirs_to_create: list[Path] = [
            self.paths.archledger_dir,
            self.paths.records_dir,
            self.paths.archive_dir,
            self.paths.build_dir,
        ]
        # Only create sections directory when the arc42 profile is enabled.
        if self._arc42_enabled():
            dirs_to_create.append(self.paths.sections_dir)
        for path in dirs_to_create:
            if not path.exists():
                created_paths.append(path)
            ensure_dir(path)

        for directory_name in sorted(set(RECORD_TYPE_TO_DIR.values())):
            directory_path = self.paths.records_dir / directory_name
            if not directory_path.exists():
                created_paths.append(directory_path)
            ensure_dir(directory_path)

        if self._arc42_enabled():
            for section_spec in MAJOR_SECTION_SPECS:
                section_id = self._format_record_id(
                    self._id_segment_for_section(section_spec),
                    section_spec.number,
                )
                section_path = (
                    self.paths.sections_dir
                    / f"{section_id}{self.config.section_extension}"
                )
                if not section_path.exists() or overwrite:
                    write_text_atomic(
                        section_path,
                        _section_document(
                            section_spec,
                            self.config.source_format,
                            record_id=section_id,
                            source_schema_version=self.config.source_schema_version,
                        ),
                    )
                    created_paths.append(section_path)

        if not self.paths.storage_meta_path.exists() or overwrite:
            meta = default_storage_meta(self.config.project_uuid, __version__)
            meta = dataclass_replace(
                meta,
                next_number=next_number_floor(
                    self.paths.archledger_dir,
                    meta.next_number,
                    source_extensions=(
                        self.config.section_extension,
                        self.config.record_extension,
                    ),
                ),
            )
            write_storage_meta(self.paths.storage_meta_path, meta)
            created_paths.append(self.paths.storage_meta_path)

        return InitResult(
            workspace_root=self.paths.workspace_root,
            config_path=self.paths.config_path,
            archledger_dir=self.paths.archledger_dir,
            created_paths=tuple(created_paths),
        )

    def status(self) -> StatusResult:
        read_storage_meta(self.paths.storage_meta_path)
        section_count = len(
            iter_source_files(
                self.paths.sections_dir,
                (self.config.section_extension,),
            )
        )
        record_directories_count = sum(
            1 for path in self.paths.records_dir.iterdir() if path.is_dir()
        )
        return StatusResult(
            workspace_root=self.paths.workspace_root,
            config_path=self.paths.config_path,
            archledger_dir=self.paths.archledger_dir,
            archive_dir=self.paths.archive_dir,
            sections_count=section_count,
            record_directories_count=record_directories_count,
            storage_meta_path=self.paths.storage_meta_path,
            build_dir=self.paths.build_dir,
        )

    def create_record(
        self,
        kind: str,
        title: str,
        **kwargs: object,
    ) -> ArchitectureRecord:
        normalized_kind = normalize_kind(kind)
        self._ensure_storage_ready()
        sequence_errors, _, missing_numbers, duplicate_numbers, _ = (
            self._ledger_sequence_findings()
        )
        if missing_numbers or duplicate_numbers:
            raise ValidationError(
                "Ledger numbering is inconsistent. Run: archledger doctor --repair"
            )
        if sequence_errors:
            raise ValidationError(
                "Storage integrity checks failed. Run: archledger doctor --repair"
            )
        meta = read_storage_meta(self.paths.storage_meta_path)
        number = next_number_floor(
            self.paths.archledger_dir,
            meta.next_number,
            source_extensions=(
                self.config.section_extension,
                self.config.record_extension,
            ),
        )
        identity_kind = self._id_segment_for_kind(normalized_kind)
        record_id = self._format_record_id(identity_kind, number)
        filename = f"{record_id}{self.config.record_extension}"
        target_dir = self.paths.records_dir / RECORD_TYPE_TO_DIR[normalized_kind]
        target_path = target_dir / filename
        while target_path.exists():
            number += 1
            record_id = self._format_record_id(identity_kind, number)
            filename = f"{record_id}{self.config.record_extension}"
            target_path = target_dir / filename
        order = self._next_order(normalized_kind)
        template_name = record_template_name_for_source_format(
            normalized_kind,
            self.config.source_format,
        )
        context = self._template_context(
            normalized_kind,
            title=title,
            order=order,
            target_path=target_path,
            **kwargs,
        )
        text = self._template_env.get_template(f"records/{template_name}").render(
            **context
        )
        write_text_atomic(target_path, text)
        self._write_counter(number + 1)
        return self._load_record_from_path(target_path)

    def list_records(
        self,
        *,
        include_draft: bool = False,
        include_superseded: bool = False,
        kind: str | None = None,
        scope: str | None = None,
        scope_kind: str | None = None,
        addon: str | None = None,
    ) -> list[ArchitectureRecord]:
        from archledger.scopes import VALID_SCOPE_KINDS

        self._ensure_storage_ready()
        all_records = self._load_records(include_sections=False)
        if kind is not None:
            normalized_kind = normalize_kind(kind)
            all_records = [
                record for record in all_records if record.type == normalized_kind
            ]
        if scope is not None or scope_kind is not None or addon is not None:
            filtered: list[ArchitectureRecord] = []
            for record in all_records:
                if record.scope is None:
                    continue
                if scope is not None and record.scope.name != scope:
                    continue
                if scope_kind is not None and scope_kind not in VALID_SCOPE_KINDS:
                    continue
                if scope_kind is not None and record.scope.kind != scope_kind:
                    continue
                if addon is not None:
                    addon_dir = addon if addon.endswith("/") else addon + "/"
                    if not any(
                        addon_dir == apply_to
                        or addon_dir.startswith(apply_to.rstrip("/") + "/")
                        or apply_to.rstrip("/") == addon
                        for apply_to in record.scope.applies_to
                    ):
                        continue
                filtered.append(record)
            all_records = filtered
        visible_records = [
            record
            for record in all_records
            if is_visible_status(
                record.status,
                include_draft=include_draft,
                include_superseded=include_superseded,
            )
        ]
        return sorted(visible_records, key=record_sort_key)

    def load_all_records(
        self,
        *,
        include_sections: bool = True,
    ) -> list[ArchitectureRecord]:
        self._ensure_storage_ready()
        records = [
            self._load_record_from_path(path) for path in self._all_record_paths()
        ]
        if include_sections:
            return sorted(records, key=record_sort_key)
        return sorted(
            [record for record in records if record.type != "section"],
            key=record_sort_key,
        )

    def get_record(self, record_id: str) -> ArchitectureRecord:
        self._ensure_storage_ready()
        for path in self._all_record_paths():
            if path.stem != record_id:
                continue
            return self._load_record_from_path(path)
        raise ValidationError(f"Record not found: {record_id}")

    def check(  # noqa: C901
        self,
        *,
        strict: bool = False,
    ) -> CheckResult:
        del strict
        self._ensure_storage_ready()
        findings_errors: list[CheckFinding] = []
        findings_warnings: list[CheckFinding] = []
        loaded_records: list[ArchitectureRecord] = []

        for path in self._all_record_paths(include_archive=True):
            try:
                record = self._load_record_from_path(path)
            except FrontMatterError as exc:
                findings_errors.append(CheckFinding("error", exc.message, path))
                continue
            except ValidationError as exc:
                findings_errors.append(CheckFinding("error", exc.message, path))
                continue

            expected_segment = self._id_segment_for_metadata(record.metadata)
            issues = validate_record(
                record,
                id_format=self.config.id_format,
                expected_segment=expected_segment,
            )
            for issue in issues:
                findings_errors.append(CheckFinding("error", issue, path))
            source_errors, source_warnings = self._source_contract_findings(record)
            findings_errors.extend(
                CheckFinding("error", message, path) for message in source_errors
            )
            findings_warnings.extend(
                CheckFinding("warning", message, path) for message in source_warnings
            )

            loaded_records.append(record)
            if record.status != "archived":
                for warning_message in content_warnings(record):
                    findings_warnings.append(
                        CheckFinding("warning", warning_message, path)
                    )
            if record.status == "archived" and not path.is_relative_to(
                self.paths.archive_dir
            ):
                findings_errors.append(
                    CheckFinding(
                        "error",
                        f"Archived record {record.id} is outside archive storage.",
                        path,
                    )
                )
            if (
                path.is_relative_to(self.paths.archive_dir)
                and record.status != "archived"
            ):
                findings_errors.append(
                    CheckFinding(
                        "error",
                        f"Archived file {record.id} must use status archived.",
                        path,
                    )
                )

        seen_ids: dict[str, Path] = {}
        for record in loaded_records:
            if record.id in seen_ids:
                findings_errors.append(
                    CheckFinding(
                        "error",
                        f"Duplicate record ID: {record.id}",
                        record.path,
                    )
                )
            else:
                seen_ids[record.id] = record.path

        loaded_ids = set(seen_ids)
        for record in loaded_records:
            parent = record.metadata.get("parent")
            if parent not in (None, "", "null") and str(parent) not in loaded_ids:
                findings_errors.append(
                    CheckFinding(
                        "error",
                        f"Parent reference points to a missing record: {parent}",
                        record.path,
                    )
                )
            # Validate link targets after all records are loaded.
            for link in record.links:
                if link.target_kind == "record" and link.target not in loaded_ids:
                    findings_warnings.append(
                        CheckFinding(
                            "warning",
                            f"Record {record.id} links entry target {link.target!r} "
                            f"does not match any loaded record ID.",
                            record.path,
                        )
                    )
                if link.target_kind == "path":
                    target_path = self.paths.workspace_root / link.target
                    if not target_path.exists():
                        findings_warnings.append(
                            CheckFinding(
                                "warning",
                                f"Record {record.id} path link target {link.target!r} "
                                "does not exist in workspace.",
                                record.path,
                            )
                        )
            if record.status == "draft":
                findings_warnings.append(
                    CheckFinding(
                        "warning",
                        f"Draft record {record.id} is excluded from the default build.",
                        record.path,
                    )
                )
            if record.type == "section" and path_in_archive(
                record.path, self.paths.archive_dir
            ):
                findings_errors.append(
                    CheckFinding(
                        "error",
                        f"Required section {record.id} must not be archived.",
                        record.path,
                    )
                )

        if self._arc42_enabled():
            for section_spec in MAJOR_SECTION_SPECS:
                section_id = self._format_record_id(
                    self._id_segment_for_section(section_spec),
                    section_spec.number,
                )
                section_paths = [
                    self.paths.sections_dir / f"{section_id}{extension}"
                    for extension in self._known_source_extensions()
                ]
                archived_section_paths = [
                    self.paths.archive_dir / "sections" / f"{section_id}{extension}"
                    for extension in self._known_source_extensions()
                ]
                if not any(path.is_file() for path in section_paths):
                    findings_errors.append(
                        CheckFinding(
                            "error",
                            f"Required section file is missing: {section_spec.key}",
                            section_paths[0],
                        )
                    )
                archived_section = next(
                    (path for path in archived_section_paths if path.is_file()),
                    None,
                )
                if archived_section is not None:
                    findings_errors.append(
                        CheckFinding(
                            "error",
                            f"Required section file is archived: {section_spec.key}",
                            archived_section,
                        )
                    )
                if any(
                    record.type != "section"
                    and record.section == section_spec.key
                    and record.status in {"accepted", "proposed"}
                    and not path_in_archive(record.path, self.paths.archive_dir)
                    for record in loaded_records
                ):
                    continue
                findings_warnings.append(
                    CheckFinding(
                        "warning",
                        f"Section {section_spec.key} has no accepted/proposed records.",
                        section_paths[0],
                    )
                )

        sequence_errors, sequence_warnings, _, _, _ = self._ledger_sequence_findings()
        findings_errors.extend(sequence_errors)
        findings_warnings.extend(sequence_warnings)

        return CheckResult(
            errors=tuple(findings_errors),
            warnings=tuple(findings_warnings),
        )

    def archive_record(self, record_id: str, *, reason: str = "") -> ArchiveResult:
        self._ensure_storage_ready()
        try:
            parse_local_ref(record_id, width=self.config.id_width)
        except IdFormatError:
            raise ValidationError(f"Invalid ledger ID: {record_id}") from None

        active_path: Path | None = None
        for path in iter_source_files(
            self.paths.records_dir,
            self._known_source_extensions(),
        ):
            if path.stem == record_id:
                active_path = path
                break

        if active_path is None:
            archived_path = self._find_archived_path(record_id)
            if archived_path is not None:
                return ArchiveResult(
                    record_id=record_id,
                    source_path=archived_path,
                    archive_path=archived_path,
                    reason=reason,
                    already_archived=True,
                )
            section_candidate = (
                self.paths.sections_dir / f"{record_id}{self.config.section_extension}"
            )
            if section_candidate.is_file():
                raise ValidationError(
                    f"Cannot archive required section {record_id}. "
                    "Sections are part of the arc42 skeleton."
                )
            raise ValidationError(f"Record not found: {record_id}")

        metadata, body = read_front_matter_document(active_path)
        relative_active = active_path.relative_to(self.paths.archledger_dir)
        archive_path = self.paths.archive_dir / relative_active
        if archive_path.exists():
            raise ValidationError(f"Archive target already exists: {archive_path}")

        metadata = bump_metadata_version(
            {
                **metadata,
                "status": "archived",
                "archived_reason": reason,
                "archived_from": str(relative_active),
            }
        )
        for field in ("date", "created_at", "updated_at", "archived_at"):
            metadata.pop(field, None)
        ensure_dir(archive_path.parent)
        write_front_matter_document(archive_path, metadata, body)
        active_path.unlink()

        return ArchiveResult(
            record_id=record_id,
            source_path=active_path,
            archive_path=archive_path,
            reason=reason,
        )

    def doctor(self, *, repair: bool = False) -> DoctorResult:
        self._ensure_storage_ready()
        meta_before = read_storage_meta(self.paths.storage_meta_path)
        repairs: list[DoctorRepair] = []

        if repair and not self.paths.archive_dir.is_dir():
            ensure_dir(self.paths.archive_dir)
            repairs.append(
                DoctorRepair(
                    kind="created_archive_dir",
                    message=f"Created archive directory: {self.paths.archive_dir}",
                    path=self.paths.archive_dir,
                )
            )
        if repair:
            identity_state = detect_identity_format_state(
                self.paths,
                self.config,
                self._known_source_extensions(),
            )
            if identity_state.legacy_paths and not identity_state.current_paths:
                examples = "\n".join(
                    f"  - {path}" for path in identity_state.legacy_paths[:10]
                )
                message = (
                    "Legacy archledger IDs were found, but no current ledgercore"
                    " local record IDs were found. Refusing repair because repair"
                    " would create tombstones against the wrong identity schema."
                    " Run: archledger migrate ids --to ledgercore --apply first."
                )
                if examples:
                    message += "\nLegacy files:\n" + examples
                return DoctorResult(
                    errors=(CheckFinding("error", message, None),),
                    warnings=(),
                    repairs=(),
                    storage_next_number_before=meta_before.next_number,
                    storage_next_number_after=meta_before.next_number,
                    highest_seen=0,
                    missing_numbers=(),
                    duplicate_numbers=(),
                )
        if repair:
            drift = find_id_format_drift(
                self.paths,
                self.config,
                self._known_source_extensions(),
            )
            if drift:
                drift_paths = "\n".join(
                    f"  - {d.path} (uses {d.detected_format.segment_mode} format, "
                    f"config expects {d.configured_format.segment_mode})"
                    for d in drift
                )
                errors_list: list[CheckFinding] = []
                errors_list.append(
                    CheckFinding(
                        "error",
                        (
                            "ID format mismatch: config uses "
                            f"{self.config.id_format.prefix}/{self.config.id_format.width}/"
                            f"{self.config.id_format.segment_mode},\n"
                            f"but {len(drift)} source files still use "
                            f"the alternate format.\n"
                            f"{drift_paths}\n"
                            "Run: archledger renumber "
                            f"--from-id-segment-mode "
                            f"{drift[0].detected_format.segment_mode} "
                            f"--id-segment-mode "
                            f"{self.config.id_segment_mode} --apply\n"
                            "Do not run doctor --repair until "
                            "renumber succeeds."
                        ),
                        None,
                    )
                )
                return DoctorResult(
                    errors=tuple(errors_list),
                    warnings=(),
                    repairs=(),
                    storage_next_number_before=meta_before.next_number,
                    storage_next_number_after=meta_before.next_number,
                    highest_seen=0,
                    missing_numbers=(),
                    duplicate_numbers=(),
                )

        (
            sequence_errors,
            sequence_warnings,
            missing_numbers,
            duplicate_numbers,
            highest_seen,
        ) = self._ledger_sequence_findings()

        if repair and not duplicate_numbers:
            for number in missing_numbers:
                section_spec = next(
                    (spec for spec in MAJOR_SECTION_SPECS if spec.number == number),
                    None,
                )
                if section_spec is not None:
                    section_id = self._format_record_id(
                        self._id_segment_for_section(section_spec),
                        section_spec.number,
                    )
                    section_path = (
                        self.paths.sections_dir
                        / f"{section_id}{self.config.section_extension}"
                    )
                    if not section_path.is_file():
                        write_text_atomic(
                            section_path,
                            _section_document(
                                section_spec,
                                self.config.source_format,
                                record_id=section_id,
                                source_schema_version=self.config.source_schema_version,
                            ),
                        )
                        repairs.append(
                            DoctorRepair(
                                kind="recreated_section",
                                message=(f"Recreated required section {section_id}"),
                                path=section_path,
                            )
                        )
                    continue
                tombstone_path, tombstone_id = self._write_archive_tombstone(number)
                repairs.append(
                    DoctorRepair(
                        kind="created_tombstone",
                        message=(f"Created archive tombstone {tombstone_id}"),
                        path=tombstone_path,
                    )
                )

            (
                sequence_errors,
                sequence_warnings,
                missing_numbers,
                duplicate_numbers,
                highest_seen,
            ) = self._ledger_sequence_findings()

        next_number_after = next_number_floor(
            self.paths.archledger_dir,
            meta_before.next_number,
            source_extensions=(
                self.config.section_extension,
                self.config.record_extension,
            ),
        )
        if repair and next_number_after != meta_before.next_number:
            self._write_counter(next_number_after)
            repairs.append(
                DoctorRepair(
                    kind="recomputed_counter",
                    message=(
                        f"Recomputed storage.yaml next_number to {next_number_after}"
                    ),
                    path=self.paths.storage_meta_path,
                    before=meta_before.next_number,
                    after=next_number_after,
                )
            )

        meta_after = read_storage_meta(self.paths.storage_meta_path)
        return DoctorResult(
            errors=tuple(sequence_errors),
            warnings=tuple(sequence_warnings),
            repairs=tuple(repairs),
            storage_next_number_before=meta_before.next_number,
            storage_next_number_after=meta_after.next_number,
            highest_seen=highest_seen,
            missing_numbers=missing_numbers,
            duplicate_numbers=duplicate_numbers,
        )

    def _find_archived_path(self, record_id: str) -> Path | None:
        for path in iter_source_files(
            self.paths.archive_dir,
            self._known_source_extensions(),
        ):
            if path.stem == record_id:
                return path
        return None

    def _numbered_source_paths(
        self, *, include_archive: bool
    ) -> list[NumberedSourcePath]:
        return _collect_numbered_source_paths(
            self.paths,
            self.config,
            self._known_source_extensions(),
            include_archive=include_archive,
        )

    def _ledger_sequence_findings(
        self,
    ) -> tuple[
        list[CheckFinding],
        list[CheckFinding],
        tuple[int, ...],
        tuple[int, ...],
        int,
    ]:
        result = _analyze_ledger_sequence(
            self.paths,
            self.config,
            self._known_source_extensions(),
            display_missing_id=self._display_missing_id,
        )
        errors = [CheckFinding(level, msg, path) for level, msg, path in result.errors]
        warnings = [
            CheckFinding(level, msg, path) for level, msg, path in result.warnings
        ]
        return (
            errors,
            warnings,
            result.missing_numbers,
            result.duplicate_numbers,
            result.highest_seen,
        )

    def _write_archive_tombstone(self, number: int) -> tuple[Path, str]:
        identity_kind = self.config.id_kind_map.get(
            "archive_tombstone",
            self.config.id_default_kind,
        )
        record_id = self._format_record_id(identity_kind, number)
        path = (
            self.paths.archive_dir
            / "tombstones"
            / f"{record_id}{self.config.record_extension}"
        )
        if path.exists():
            return path, record_id
        metadata = {
            "schema_version": self.config.source_schema_version,
            "id": record_id,
            "kind": identity_kind,
            "type": "archive_tombstone",
            "title": f"Archived placeholder for missing ledger ID {record_id}",
            "status": "archived",
            "section": "risks_and_technical_debt",
            "order": number,
            "version": 1,
            "body_format": self.config.source_format,
            "archived_reason": (
                "Created by archledger doctor --repair for a missing ledger number."
            ),
        }
        body = (
            "This tombstone preserves a ledger number whose original source fragment "
            "is no longer present. It was created automatically by "
            "`archledger doctor --repair`.\n"
        )
        ensure_dir(path.parent)
        write_front_matter_document(path, metadata, body)
        return path, record_id

    def _id_segment_for_kind(self, kind: str) -> str:
        return normalize_resource_kind(
            self.config.id_kind_map.get(kind, self.config.id_default_kind)
        )

    def _id_segment_for_section(self, section_spec: SectionSpec) -> str:
        del section_spec
        return normalize_resource_kind(
            self.config.id_kind_map.get("section", self.config.id_default_kind)
        )

    def _id_segment_for_metadata(self, metadata: dict[str, object]) -> str:
        return identity_kind_for_metadata(
            metadata,
            default_kind=self.config.id_default_kind,
            kind_map=self.config.id_kind_map,
        )

    def _display_missing_id(self, number: int) -> str:
        return f"<kind>-{number:0{self.config.id_width}d}"

    def _format_record_id(self, kind: str, number: int) -> str:
        return format_local_id(kind, number, width=self.config.id_width)

    def _global_ref(self, record_id: str) -> str:
        return global_ref_for(
            record_id, self.config.ledger_code, width=self.config.id_width
        )

    def _template_context(
        self,
        kind: str,
        *,
        title: str,
        order: int,
        target_path: Path,
        **kwargs: object,
    ) -> dict[str, object]:
        spec = RECORD_TYPES[kind]
        status = kwargs.get("status", spec.default_status)
        section = kwargs.get("section") or RECORD_TYPE_TO_DEFAULT_SECTION[kind]
        parent = kwargs.get("parent")
        if kind == "diagram" and not kwargs.get("diagram_type"):
            kwargs = {**kwargs, "diagram_type": self.config.diagram_default_type}
        context: dict[str, object] = {
            "schema_version": self.config.source_schema_version,
            "id": target_path.stem,
            "kind": self._id_segment_for_kind(kind),
            "type": kind,
            "title": title,
            "status": status,
            "section": section,
            "order": order,
            "version": 1,
            "body_format": self.config.source_format,
            "parent": "null" if parent in (None, "") else parent,
            "level": kwargs.get("level", spec.default_level),
        }
        context.update(
            spec.context_factory(
                RecordContextInput(
                    title=title,
                    status=str(status),
                    section=str(section),
                    parent=None if parent in (None, "") else str(parent),
                    kwargs=kwargs,
                )
            )
        )
        return context

    def _next_order(self, kind: str) -> int:
        existing_orders = [
            record.order
            for record in self._load_records(include_sections=False)
            if record.type == kind
        ]
        return (max(existing_orders) + 10) if existing_orders else 10

    def _load_records(self, *, include_sections: bool) -> list[ArchitectureRecord]:
        records = [
            self._load_record_from_path(path) for path in self._all_record_paths()
        ]
        if include_sections:
            return records
        return [record for record in records if record.type != "section"]

    def _all_record_paths(self, *, include_archive: bool = False) -> list[Path]:
        paths = [
            *iter_source_files(
                self.paths.sections_dir,
                self._known_source_extensions(),
            ),
            *iter_source_files(
                self.paths.records_dir,
                self._known_source_extensions(),
            ),
        ]
        if include_archive:
            paths.extend(
                iter_source_files(
                    self.paths.archive_dir,
                    self._known_source_extensions(),
                )
            )
        return paths

    def _load_record_from_path(self, path: Path) -> ArchitectureRecord:
        metadata, body = read_front_matter_document(path)
        schema_version_value = metadata.get("schema_version")
        schema_version = (
            schema_version_value
            if isinstance(schema_version_value, int)
            and not isinstance(schema_version_value, bool)
            else self.config.source_schema_version
        )
        required_fields: tuple[str, ...] = REQUIRED_RECORD_FIELDS
        if schema_version < 3:
            required_fields = tuple(
                field for field in REQUIRED_RECORD_FIELDS if field != "kind"
            )
        missing_fields = [field for field in required_fields if field not in metadata]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValidationError(f"Missing required key(s): {missing}")

        title = metadata["title"]
        status = metadata["status"]
        section = metadata["section"]
        order = metadata["order"]
        record_type = metadata["type"]
        raw_kind = metadata.get("kind")
        if isinstance(raw_kind, str) and raw_kind.strip():
            record_kind = normalize_resource_kind(raw_kind)
        else:
            record_kind = self._id_segment_for_metadata(metadata)
            metadata = {**metadata, "kind": record_kind}
        record_id = metadata["id"]
        required_strings = (title, status, section, record_type, record_id, record_kind)
        if not all(isinstance(value, str) for value in required_strings):
            raise ValidationError("Required string fields must be strings.")
        if isinstance(order, bool) or not isinstance(order, int):
            raise ValidationError("Required key order must be an integer.")

        record = ArchitectureRecord(
            id=cast(str, record_id),
            kind=record_kind,
            type=cast(str, record_type),
            title=cast(str, title),
            status=cast(str, status),
            section=cast(str, section),
            order=order,
            path=path,
            metadata=metadata,
            body=body,
            source_refs=normalize_source_refs(
                cast(str, record_id),
                metadata.get("source_refs"),
                workspace_root=self.paths.workspace_root,
                require_exists=cast(str, status) != "archived",
            )[0],
            links=normalize_links(
                cast(str, record_id),
                metadata.get("links"),
            )[0],
            test_refs=normalize_test_refs(
                cast(str, record_id),
                metadata.get("test_refs"),
                workspace_root=self.paths.workspace_root,
            )[0],
            scope=normalize_scope(
                cast(str, record_id),
                metadata.get("scope"),
                workspace_root=self.paths.workspace_root,
            )[0],
        )
        return record

    def _ensure_storage_ready(self) -> None:
        if not self.paths.storage_meta_path.is_file():
            raise StorageError(
                "Missing storage metadata file: "
                f"{self.paths.storage_meta_path}. Run: archledger init"
            )
        if self._arc42_enabled() and not self.paths.sections_dir.is_dir():
            raise StorageError(
                "archledger storage layout is incomplete. Run: archledger init"
            )
        if not self.paths.records_dir.is_dir():
            raise StorageError(
                "archledger storage layout is incomplete. Run: archledger init"
            )

    def _arc42_enabled(self) -> bool:
        return "arc42" in self.config.profiles.profiles.enabled

    def _write_counter(self, next_number: int) -> None:
        current_meta = read_storage_meta(self.paths.storage_meta_path)
        write_storage_meta(
            self.paths.storage_meta_path,
            dataclass_replace(
                current_meta,
                storage_version=3,
                version=current_meta.version + 1,
                next_number=max(
                    next_number_floor(
                        self.paths.archledger_dir,
                        current_meta.next_number,
                        source_extensions=(
                            self.config.section_extension,
                            self.config.record_extension,
                        ),
                    ),
                    next_number,
                ),
            ),
        )

    def _source_contract_findings(
        self,
        record: ArchitectureRecord,
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        source_format = self.config.source_format
        config_version = self.config.config_version
        schema_version = record.metadata.get("schema_version")
        body_format = record.metadata.get("body_format")
        version = record.metadata.get("version")

        if schema_version is None:
            if config_version >= 4:
                errors.append(f"Record {record.id} is missing schema_version.")
        elif isinstance(schema_version, bool) or not isinstance(schema_version, int):
            errors.append(f"Record {record.id} schema_version must be an integer.")
        elif schema_version != self.config.source_schema_version:
            message = (
                f"Record {record.id} schema_version {schema_version} does not match "
                f"source.schema_version {self.config.source_schema_version}."
            )
            if config_version >= 4:
                errors.append(message)
            else:
                warnings.append(message)

        current_schema = (
            isinstance(schema_version, int)
            and not isinstance(schema_version, bool)
            and schema_version >= 4
        )
        if version is None:
            if current_schema or self.config.source_schema_version >= 4:
                errors.append(f"Record {record.id} is missing version.")
        elif isinstance(version, bool) or not isinstance(version, int) or version < 1:
            errors.append(f"Record {record.id} version must be a positive integer.")

        legacy_fields = ("date", "created_at", "updated_at", "archived_at")
        present_legacy = [field for field in legacy_fields if field in record.metadata]
        if present_legacy:
            message = (
                f"Record {record.id} contains legacy timestamp field(s): "
                + ", ".join(present_legacy)
                + ". Run: archledger migrate metadata --to versioned --apply"
            )
            if current_schema:
                errors.append(message)
            else:
                warnings.append(message)

        if body_format is None:
            if config_version >= 4:
                errors.append(f"Record {record.id} is missing body_format.")
        elif not isinstance(body_format, str):
            errors.append(f"Record {record.id} body_format must be a string.")
        else:
            normalized_body_format = body_format.strip().lower()
            if normalized_body_format not in VALID_BODY_FORMATS:
                errors.append(
                    f"Record {record.id} body_format must be one of: "
                    + ", ".join(sorted(VALID_BODY_FORMATS))
                    + "."
                )
            elif normalized_body_format != source_format:
                message = (
                    f"Record {record.id} body_format {normalized_body_format!r} does "
                    f"not match source format {source_format!r}."
                )
                if config_version >= 4:
                    errors.append(message)
                else:
                    warnings.append(message)

        _, source_ref_warnings = normalize_source_refs(
            record.id,
            record.metadata.get("source_refs"),
            workspace_root=self.paths.workspace_root,
            require_exists=record.status != "archived",
        )
        warnings.extend(source_ref_warnings)

        return errors, warnings

    def _known_source_extensions(self) -> tuple[str, ...]:
        return known_source_extensions(self.config)


def _section_document(
    section_spec: SectionSpec,
    source_format: str,
    *,
    record_id: str,
    source_schema_version: int = CURRENT_SOURCE_SCHEMA_VERSION,
    version: int = 1,
) -> str:
    lines = [
        "---",
        f"schema_version: {source_schema_version}",
        f"id: {record_id}",
        f"kind: {record_id.split('-', 1)[0]}",
        "type: section",
        f"section: {section_spec.key}",
        f"title: {section_spec.title}",
        f"order: {section_spec.order}",
        "status: accepted",
        f"version: {version}",
        f"body_format: {source_format}",
        "---",
        "",
        section_body_placeholder_for_source_format(source_format),
        "",
    ]
    return "\n".join(lines)


def path_in_archive(path: Path, archive_dir: Path) -> bool:
    return is_relative_to(path, archive_dir)
