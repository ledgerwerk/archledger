from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from jinja2 import Environment, PackageLoader, select_autoescape

from archledger import __version__
from archledger.errors import StorageError, ValidationError
from archledger.model import (
    CURRENT_SOURCE_SCHEMA_VERSION,
    MAJOR_SECTION_SPECS,
    PLACEHOLDER_SNIPPETS,
    RECORD_TYPE_TO_DEFAULT_SECTION,
    RECORD_TYPE_TO_DIR,
    RECORD_TYPE_TO_FILENAME_PREFIX,
    REQUIRED_RECORD_FIELDS,
    VALID_BODY_FORMATS,
    ArchitectureRecord,
    SourceRef,
    SectionSpec,
    default_extension_for_source_format,
    filename_for,
    is_visible_status,
    section_body_placeholder_for_source_format,
    normalize_kind,
    record_sort_key,
    record_template_name_for_source_format,
    section_filename_for,
    validate_record,
)
from archledger.storage.common import ensure_dir, utc_now_iso, write_text
from archledger.storage.frontmatter import (
    FrontMatterError,
    iter_source_files,
    read_front_matter_document,
)
from archledger.storage.meta import (
    StorageMeta,
    default_storage_meta,
    read_storage_meta,
    recompute_next_numbers,
    write_storage_meta,
)
from archledger.storage.paths import ProjectPaths
from archledger.storage.project_config import ProjectConfig

ALLOWED_CONSTRAINT_CATEGORIES = frozenset(
    {"technical", "organizational", "regulatory", "convention"}
)
ALLOWED_RISK_LEVELS = frozenset({"low", "medium", "high"})


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
                write_text(
                    section_path,
                    _section_document(
                        section_spec,
                        self.config.source_format,
                        source_schema_version=self.config.source_schema_version,
                        created_at=created_at,
                    ),
                )
                created_paths.append(section_path)

        meta = default_storage_meta(self.config.project_uuid, __version__)
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
        next_numbers = recompute_next_numbers(
            self.paths.records_dir,
            record_extensions=(self.config.record_extension,),
        )
        prefix = RECORD_TYPE_TO_FILENAME_PREFIX[normalized_kind]
        number = next_numbers[prefix]
        filename = filename_for(
            normalized_kind,
            number,
            extension=self.config.record_extension,
        )
        target_dir = self.paths.records_dir / RECORD_TYPE_TO_DIR[normalized_kind]
        target_path = target_dir / filename
        while target_path.exists():
            number += 1
            filename = filename_for(
                normalized_kind,
                number,
                extension=self.config.record_extension,
            )
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
        text = self._template_env.get_template(
            f"records/{template_name}"
        ).render(**context)
        write_text(target_path, text)
        self._write_recomputed_counters()
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
                record
                for record in all_records
                if record.type == normalized_kind
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
            self._load_record_from_path(path)
            for path in self._all_record_paths()
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
            warning_message = self._placeholder_warning(record)
            if warning_message is not None:
                findings_warnings.append(CheckFinding("warning", warning_message, path))
            for warning_message in self._content_warnings(record):
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
            if record.type == "adr" and not _non_empty_sequence(
                record.metadata.get("deciders")
            ):
                findings_warnings.append(
                    CheckFinding(
                        "warning",
                        f"ADR {record.id} has no deciders.",
                        record.path,
                    )
                )
            if record.type == "risk" and not _non_empty_text(
                record.metadata.get("mitigation")
            ):
                findings_warnings.append(
                    CheckFinding(
                        "warning",
                        f"Risk {record.id} has no mitigation.",
                        record.path,
                    )
                )
            if record.type == "glossary_term" and not _non_empty_text(
                record.metadata.get("definition")
            ):
                findings_warnings.append(
                    CheckFinding(
                        "warning",
                        f"Glossary term {record.id} has no definition.",
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
            self._write_recomputed_counters()
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
        status = kwargs.get("status", "draft")
        section = kwargs.get("section") or RECORD_TYPE_TO_DEFAULT_SECTION[kind]
        parent = kwargs.get("parent")
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
            "level": kwargs.get("level", 1),
        }
        if kind == "requirement":
            context["source"] = ""
            context["priority"] = "must"
            context["stakeholders"] = []
            context["quality_goals"] = []
        elif kind == "stakeholder":
            context["contact"] = ""
            context["expectations"] = []
        elif kind == "quality_goal":
            context["priority"] = 1
            context["scenario"] = ""
        elif kind == "constraint":
            context["category"] = "technical"
            context["impact"] = ""
        elif kind == "context_interface":
            context["context_kind"] = kwargs.get("context_kind", "technical")
            context["partner"] = kwargs.get("partner", "")
            context["inputs"] = []
            context["outputs"] = []
            context["channels"] = []
        elif kind == "strategy_item":
            context["drivers"] = []
            context["constraints"] = []
            context["related_adrs"] = []
        elif kind == "white_box":
            context["diagram"] = None
            context["quality_characteristics"] = []
            context["tags"] = []
        elif kind == "black_box":
            context["interfaces"] = []
            context["location"] = []
            context["fulfilled_requirements"] = []
            context["risks"] = []
            context["tags"] = []
        elif kind == "interface":
            context["providers"] = []
            context["consumers"] = []
            context["protocol"] = ""
        elif kind == "runtime_scenario":
            context["participants"] = []
            context["trigger"] = ""
            context["result"] = ""
        elif kind == "infrastructure":
            context["environment"] = kwargs.get("environment", "development")
            context["maps_building_blocks"] = []
        elif kind == "concept":
            context["applies_to"] = []
        elif kind == "adr":
            context["status"] = kwargs.get("status", "proposed")
            context["deciders"] = []
            context["supersedes"] = []
            context["related"] = []
            context["tags"] = []
        elif kind == "quality_requirement":
            context["category"] = "reliability"
            context["source"] = ""
            context["measure"] = ""
            context["scenarios"] = []
        elif kind == "quality_scenario":
            context["quality"] = kwargs.get("quality", "")
            context["source"] = ""
            context["stimulus"] = ""
            context["environment"] = kwargs.get("environment", "normal_development")
            context["artifact"] = ""
            context["response"] = ""
            context["response_measure"] = ""
        elif kind == "risk":
            context["severity"] = "medium"
            context["probability"] = "medium"
            context["mitigation"] = ""
        elif kind == "glossary_term":
            context["term"] = title
            context["definition"] = ""
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
            self._load_record_from_path(path)
            for path in self._all_record_paths()
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
            source_refs=_normalize_source_refs(
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

    def _write_recomputed_counters(self) -> None:
        current_meta = read_storage_meta(self.paths.storage_meta_path)
        refreshed_meta = StorageMeta(
            storage_version=current_meta.storage_version,
            created_with_archledger=current_meta.created_with_archledger,
            project_uuid=current_meta.project_uuid,
            created_at=current_meta.created_at,
            next_numbers=recompute_next_numbers(
                self.paths.records_dir,
                record_extensions=(self.config.record_extension,),
            ),
        )
        write_storage_meta(self.paths.storage_meta_path, refreshed_meta)

    def _placeholder_warning(self, record: ArchitectureRecord) -> str | None:
        if record.type == "section":
            return None
        stripped_body = record.body.strip()
        if not stripped_body:
            return None
        if any(snippet in stripped_body for snippet in PLACEHOLDER_SNIPPETS):
            return f"Record body is placeholder text for {record.id}."
        return None

    def _content_warnings(self, record: ArchitectureRecord) -> list[str]:
        checker = _CONTENT_WARNING_CHECKERS.get(record.type)
        warnings = [] if checker is None else checker(record)
        warnings.extend(self._body_syntax_warnings(record))
        return warnings

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

        _, source_ref_warnings = _normalize_source_refs(
            record.id,
            record.metadata.get("source_refs"),
            workspace_root=self.paths.workspace_root,
        )
        warnings.extend(source_ref_warnings)

        return errors, warnings

    def _body_syntax_warnings(self, record: ArchitectureRecord) -> list[str]:
        body_format_value = record.metadata.get("body_format", self.config.source_format)
        if not isinstance(body_format_value, str):
            return []
        body_format = body_format_value.strip().lower()
        if body_format == "markdown":
            if "[discrete]" in record.body and "\n===" in record.body:
                return [
                    f"Markdown record {record.id} contains AsciiDoc-style discrete headings."
                ]
            return []
        if body_format == "asciidoc":
            if any(
                line.startswith("## ")
                for line in record.body.splitlines()
                if not line.startswith("```")
            ):
                return [f"AsciiDoc record {record.id} contains Markdown headings."]
        return []


def _normalize_source_refs(
    record_id: str,
    value: object,
    *,
    workspace_root: Path,
) -> tuple[tuple[SourceRef, ...], list[str]]:
    if value is None:
        return (), []
    if not isinstance(value, list):
        return (), [f"Record {record_id} source_refs must be a list."]

    refs: list[SourceRef] = []
    warnings: list[str] = []
    for index, entry in enumerate(value, start=1):
        normalized_ref, entry_warnings = _normalize_source_ref_entry(
            record_id,
            entry,
            index=index,
            workspace_root=workspace_root,
        )
        warnings.extend(entry_warnings)
        if normalized_ref is not None:
            refs.append(normalized_ref)
    return tuple(refs), warnings


def _normalize_source_ref_entry(
    record_id: str,
    entry: object,
    *,
    index: int,
    workspace_root: Path,
) -> tuple[SourceRef | None, list[str]]:
    if isinstance(entry, str):
        path_text, _, symbol = entry.partition("#")
        symbols = () if not symbol else (symbol,)
        return _build_source_ref(
            record_id,
            path_text,
            symbols,
            "",
            index=index,
            workspace_root=workspace_root,
        )

    if not isinstance(entry, dict):
        return (
            None,
            [
                f"Record {record_id} source_refs entry {index} must be a string or mapping."
            ],
        )

    raw_path = entry.get("path")
    raw_symbols = entry.get("symbols", ())
    raw_reason = entry.get("reason", "")
    if not isinstance(raw_symbols, list) and not isinstance(raw_symbols, tuple):
        return (
            None,
            [
                f"Record {record_id} source_refs entry {index} symbols must be a list of strings."
            ],
        )
    symbols: list[str] = []
    for symbol in raw_symbols:
        if not isinstance(symbol, str) or not symbol.strip():
            return (
                None,
                [
                    f"Record {record_id} source_refs entry {index} symbols must contain only non-empty strings."
                ],
            )
        symbols.append(symbol.strip())
    if not isinstance(raw_reason, str):
        return (
            None,
            [f"Record {record_id} source_refs entry {index} reason must be a string."],
        )
    return _build_source_ref(
        record_id,
        raw_path,
        tuple(symbols),
        raw_reason.strip(),
        index=index,
        workspace_root=workspace_root,
    )


def _build_source_ref(
    record_id: str,
    raw_path: object,
    symbols: tuple[str, ...],
    reason: str,
    *,
    index: int,
    workspace_root: Path,
) -> tuple[SourceRef | None, list[str]]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return (
            None,
            [f"Record {record_id} source_refs entry {index} must define a non-empty path."],
        )
    original_path = raw_path.strip()
    is_directory_ref = original_path.endswith("/")
    normalized_path = original_path.rstrip("/")
    pure_path = Path(normalized_path)
    if pure_path.is_absolute():
        return (
            None,
            [f"Record {record_id} source_refs entry {index} path must be relative."],
        )
    if ".." in pure_path.parts:
        return (
            None,
            [
                f"Record {record_id} source_refs entry {index} path must not contain '..': {original_path}"
            ],
        )
    posix_path = pure_path.as_posix()
    if not posix_path or posix_path == ".":
        return (
            None,
            [f"Record {record_id} source_refs entry {index} path must not be empty."],
        )
    if not is_directory_ref and not (workspace_root / pure_path).exists():
        return (
            None,
            [
                f"Record {record_id} source_refs entry {index} path does not exist: {posix_path}"
            ],
        )
    if is_directory_ref:
        posix_path = f"{posix_path}/"
    return (SourceRef(path=posix_path, symbols=symbols, reason=reason), [])


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
        f"id: section_{section_spec.key}",
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


def _non_empty_sequence(value: object) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def _non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _contains_adr_sections(body: str) -> bool:
    body_lower = body.lower()
    return all(
        any(heading in body_lower for heading in headings)
        for headings in (
            ("## context", "=== context"),
            ("## decision", "=== decision"),
            ("## consequences", "=== consequences"),
        )
    )


def _looks_measurable(value: str) -> bool:
    lowered = value.lower()
    if any(char.isdigit() for char in lowered):
        return True
    indicators = (
        "%",
        "percent",
        "ms",
        "millisecond",
        "second",
        "minute",
        "hour",
        "count",
        "byte",
        "identical",
        "latency",
        "throughput",
        "less than",
        "greater than",
        "at least",
        "at most",
        "zero",
        "one",
        "two",
    )
    return any(indicator in lowered for indicator in indicators)


def _quality_goal_warnings(record: ArchitectureRecord) -> list[str]:
    if _non_empty_text(record.metadata.get("scenario")):
        return []
    return [f"Quality goal {record.id} has no scenario."]


def _stakeholder_warnings(record: ArchitectureRecord) -> list[str]:
    if _non_empty_sequence(record.metadata.get("expectations")):
        return []
    return [f"Stakeholder {record.id} has no expectations."]


def _constraint_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    if not _non_empty_text(record.metadata.get("impact")):
        warnings.append(f"Constraint {record.id} has no impact.")
    category = record.metadata.get("category")
    if category not in ALLOWED_CONSTRAINT_CATEGORIES:
        warnings.append(f"Constraint {record.id} has unsupported category: {category}")
    return warnings


def _context_interface_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    if not _non_empty_text(record.metadata.get("partner")):
        warnings.append(f"Context interface {record.id} has no partner.")
    if not any(
        _non_empty_sequence(record.metadata.get(field))
        for field in ("inputs", "outputs", "channels")
    ):
        warnings.append(
            f"Context interface {record.id} has no inputs, outputs, or channels."
        )
    return warnings


def _white_box_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    level = record.metadata.get("level")
    if isinstance(level, bool) or not isinstance(level, int) or level < 1:
        warnings.append(f"White box {record.id} must have a positive integer level.")
    parent = record.metadata.get("parent")
    if isinstance(level, int) and level > 1 and parent in (None, "", "null"):
        warnings.append(f"White box {record.id} at level > 1 requires a parent.")
    return warnings


def _black_box_warnings(record: ArchitectureRecord) -> list[str]:
    if record.metadata.get("parent") not in (None, "", "null"):
        return []
    return [
        (
            f"Black box {record.id} should declare a parent unless it is "
            "intentionally top-level external."
        )
    ]


def _runtime_scenario_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    if not _non_empty_sequence(record.metadata.get("participants")):
        warnings.append(f"Runtime scenario {record.id} has no participants.")
    if not _non_empty_text(record.metadata.get("trigger")):
        warnings.append(f"Runtime scenario {record.id} has no trigger.")
    return warnings


def _infrastructure_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    environment = record.metadata.get("environment")
    if not _non_empty_text(environment):
        warnings.append(f"Infrastructure {record.id} has no environment.")
    if (
        isinstance(environment, str)
        and environment.strip().lower() == "production"
        and not _non_empty_sequence(record.metadata.get("maps_building_blocks"))
    ):
        warnings.append(
            
                f"Infrastructure {record.id} in production must map building "
                "blocks explicitly."
            
        )
    return warnings


def _adr_warnings(record: ArchitectureRecord) -> list[str]:
    if _contains_adr_sections(record.body):
        return []
    return [
        (
            f"ADR {record.id} should contain Context, Decision, and "
            "Consequences sections."
        )
    ]


def _quality_scenario_warnings(record: ArchitectureRecord) -> list[str]:
    response_measure = record.metadata.get("response_measure")
    if not _non_empty_text(response_measure):
        return [f"Quality scenario {record.id} has no response_measure."]
    if isinstance(response_measure, str) and not _looks_measurable(response_measure):
        return [
            f"Quality scenario {record.id} response_measure should be measurable."
        ]
    return []


def _risk_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    severity = record.metadata.get("severity")
    probability = record.metadata.get("probability")
    if severity not in ALLOWED_RISK_LEVELS:
        warnings.append(f"Risk {record.id} has unsupported severity: {severity}")
    if probability not in ALLOWED_RISK_LEVELS:
        warnings.append(
            f"Risk {record.id} has unsupported probability: {probability}"
        )
    return warnings


_CONTENT_WARNING_CHECKERS: dict[str, Callable[[ArchitectureRecord], list[str]]] = {
    "quality_goal": _quality_goal_warnings,
    "stakeholder": _stakeholder_warnings,
    "constraint": _constraint_warnings,
    "context_interface": _context_interface_warnings,
    "white_box": _white_box_warnings,
    "black_box": _black_box_warnings,
    "runtime_scenario": _runtime_scenario_warnings,
    "infrastructure": _infrastructure_warnings,
    "adr": _adr_warnings,
    "quality_scenario": _quality_scenario_warnings,
    "risk": _risk_warnings,
}
