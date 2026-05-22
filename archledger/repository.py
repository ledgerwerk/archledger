from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from jinja2 import Environment, PackageLoader, select_autoescape

from archledger import __version__
from archledger.checks import content_warnings
from archledger.errors import StorageError, ValidationError
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
    filename_for,
    is_visible_status,
    normalize_kind,
    record_sort_key,
    record_template_name_for_source_format,
    section_body_placeholder_for_source_format,
    section_filename_for,
    validate_record,
)
from archledger.record_types import RecordContextInput
from archledger.ids import format_ledger_id
from archledger.source_refs import normalize_source_refs
from archledger.storage.common import ensure_dir, utc_now_iso, write_text_atomic
from archledger.storage.frontmatter import (
    FrontMatterError,
    iter_source_files,
    read_front_matter_document,
)
from archledger.storage.meta import (
    StorageMeta,
    default_storage_meta,
    read_storage_meta,
    recompute_next_number,
    write_storage_meta,
)
from archledger.storage.paths import ProjectPaths
from archledger.storage.project_config import ProjectConfig


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
    repaired_counters: bool = False

    def has_failures(self, *, strict: bool) -> bool:
        return bool(self.errors) or (strict and bool(self.warnings))


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
        created_at = utc_now_iso()
        for path in (
            self.paths.archledger_dir,
            self.paths.sections_dir,
            self.paths.records_dir,
            self.paths.build_dir,
        ):
            if not path.exists():
                created_paths.append(path)
            ensure_dir(path)

        for directory_name in sorted(set(RECORD_TYPE_TO_DIR.values())):
            directory_path = self.paths.records_dir / directory_name
            if not directory_path.exists():
                created_paths.append(directory_path)
            ensure_dir(directory_path)

        for section_spec in MAJOR_SECTION_SPECS:
            section_path = self.paths.sections_dir / section_filename_for(
                section_spec,
                self.config.section_extension,
            )
            if not section_path.exists() or overwrite:
                write_text_atomic(
                    section_path,
                    _section_document(
                        section_spec,
                        self.config.source_format,
                        source_schema_version=self.config.source_schema_version,
                        created_at=created_at,
                    ),
                )
                created_paths.append(section_path)

        if not self.paths.storage_meta_path.exists() or overwrite:
            meta = default_storage_meta(self.config.project_uuid, __version__)
            meta = StorageMeta(
                storage_version=meta.storage_version,
                created_with_archledger=meta.created_with_archledger,
                project_uuid=meta.project_uuid,
                created_at=meta.created_at,
                next_number=recompute_next_number(
                    self.paths.archledger_dir,
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
        number = recompute_next_number(
            self.paths.archledger_dir,
            source_extensions=(
                self.config.section_extension,
                self.config.record_extension,
            ),
        )
        filename = filename_for(number, extension=self.config.record_extension)
        target_dir = self.paths.records_dir / RECORD_TYPE_TO_DIR[normalized_kind]
        target_path = target_dir / filename
        while target_path.exists():
            number += 1
            filename = filename_for(number, extension=self.config.record_extension)
            target_path = target_dir / filename
        order = self._next_order(normalized_kind)
        created_at = utc_now_iso()
        template_name = record_template_name_for_source_format(
            normalized_kind,
            self.config.source_format,
        )
        context = self._template_context(
            normalized_kind,
            title=title,
            order=order,
            created_at=created_at,
            target_path=target_path,
            **kwargs,
        )
        text = self._template_env.get_template(f"records/{template_name}").render(
            **context
        )
        write_text_atomic(target_path, text)
        self._write_recomputed_counter()
        return self._load_record_from_path(target_path)

    def list_records(
        self,
        *,
        include_draft: bool = False,
        include_superseded: bool = False,
        kind: str | None = None,
    ) -> list[ArchitectureRecord]:
        self._ensure_storage_ready()
        all_records = self._load_records(include_sections=False)
        if kind is not None:
            normalized_kind = normalize_kind(kind)
            all_records = [
                record for record in all_records if record.type == normalized_kind
            ]
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

    def check(
        self,
        *,
        strict: bool = False,
        repair_counters: bool = False,
    ) -> CheckResult:
        del strict
        self._ensure_storage_ready()
        findings_errors: list[CheckFinding] = []
        findings_warnings: list[CheckFinding] = []
        loaded_records: list[ArchitectureRecord] = []

        for path in self._all_record_paths():
            try:
                record = self._load_record_from_path(path)
            except FrontMatterError as exc:
                findings_errors.append(CheckFinding("error", exc.message, path))
                continue
            except ValidationError as exc:
                findings_errors.append(CheckFinding("error", exc.message, path))
                continue

            issues = validate_record(record)
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
            for warning_message in content_warnings(record):
                findings_warnings.append(CheckFinding("warning", warning_message, path))

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
            if record.status == "draft":
                findings_warnings.append(
                    CheckFinding(
                        "warning",
                        f"Draft record {record.id} is excluded from the default build.",
                        record.path,
                    )
                )

        for section_spec in MAJOR_SECTION_SPECS:
            if any(
                record.type != "section"
                and record.section == section_spec.key
                and record.status in {"accepted", "proposed"}
                for record in loaded_records
            ):
                continue
            findings_warnings.append(
                CheckFinding(
                    "warning",
                    f"Section {section_spec.key} has no accepted/proposed records.",
                    self.paths.sections_dir
                    / section_filename_for(section_spec, self.config.section_extension),
                )
            )

        repaired_counters = False
        if repair_counters:
            self._write_recomputed_counter()
            repaired_counters = True

        return CheckResult(
            errors=tuple(findings_errors),
            warnings=tuple(findings_warnings),
            repaired_counters=repaired_counters,
        )

    def _template_context(
        self,
        kind: str,
        *,
        title: str,
        order: int,
        created_at: str,
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
            "type": kind,
            "title": title,
            "status": status,
            "section": section,
            "order": order,
            "created_at": created_at,
            "updated_at": created_at,
            "date": created_at[:10],
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

    def _all_record_paths(self) -> list[Path]:
        return [
            *iter_source_files(
                self.paths.sections_dir,
                (self.config.section_extension,),
            ),
            *iter_source_files(
                self.paths.records_dir,
                (self.config.record_extension,),
            ),
        ]

    def _load_record_from_path(self, path: Path) -> ArchitectureRecord:
        metadata, body = read_front_matter_document(path)
        missing_fields = [
            field for field in REQUIRED_RECORD_FIELDS if field not in metadata
        ]
        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValidationError(f"Missing required key(s): {missing}")

        title = metadata["title"]
        status = metadata["status"]
        section = metadata["section"]
        order = metadata["order"]
        record_type = metadata["type"]
        record_id = metadata["id"]
        required_strings = (title, status, section, record_type, record_id)
        if not all(isinstance(value, str) for value in required_strings):
            raise ValidationError("Required string fields must be strings.")
        if isinstance(order, bool) or not isinstance(order, int):
            raise ValidationError("Required key order must be an integer.")

        record = ArchitectureRecord(
            id=cast(str, record_id),
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
            )[0],
        )
        return record

    def _ensure_storage_ready(self) -> None:
        if not self.paths.storage_meta_path.is_file():
            raise StorageError(
                "Missing storage metadata file: "
                f"{self.paths.storage_meta_path}. Run: archledger init"
            )
        if not self.paths.sections_dir.is_dir() or not self.paths.records_dir.is_dir():
            raise StorageError(
                "archledger storage layout is incomplete. Run: archledger init"
            )

    def _write_recomputed_counter(self) -> None:
        current_meta = read_storage_meta(self.paths.storage_meta_path)
        refreshed_meta = StorageMeta(
            storage_version=current_meta.storage_version,
            created_with_archledger=current_meta.created_with_archledger,
            project_uuid=current_meta.project_uuid,
            created_at=current_meta.created_at,
            next_number=recompute_next_number(
                self.paths.archledger_dir,
                source_extensions=(
                    self.config.section_extension,
                    self.config.record_extension,
                ),
            ),
        )
        write_storage_meta(self.paths.storage_meta_path, refreshed_meta)

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
        date = record.metadata.get("date")

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

        if date is None:
            if config_version >= 4:
                errors.append(f"Record {record.id} is missing date.")
        elif not isinstance(date, str) or not date.strip():
            errors.append(f"Record {record.id} date must be a non-empty string.")

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
        )
        warnings.extend(source_ref_warnings)

        return errors, warnings


def _section_document(
    section_spec: SectionSpec,
    source_format: str,
    *,
    source_schema_version: int = CURRENT_SOURCE_SCHEMA_VERSION,
    created_at: str | None = None,
) -> str:
    timestamp = utc_now_iso() if created_at is None else created_at
    lines = [
        "---",
        f"schema_version: {source_schema_version}",
        f"id: {format_ledger_id(section_spec.number)}",
        "type: section",
        f"section: {section_spec.key}",
        f"title: {section_spec.title}",
        f"order: {section_spec.order}",
        "status: accepted",
        f'date: "{timestamp[:10]}"',
        f"body_format: {source_format}",
        f'created_at: "{timestamp}"',
        f'updated_at: "{timestamp}"',
        "---",
        "",
        section_body_placeholder_for_source_format(source_format),
        "",
    ]
    return "\n".join(lines)
