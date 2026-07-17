from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

from archledger.errors import StorageError
from archledger.model import (
    VALID_OUTPUT_FORMATS,
    ArchitectureRecord,
    default_document_filename_for_output_format,
    is_visible_status,
)
from archledger.storage.paths import ProjectPaths
from archledger.storage.paths import is_relative_to as _is_relative_to
from archledger.storage.project_config import ProjectConfig

SOURCE_STATE_SCHEMA = "archledger.source-state.v3"


@dataclass(frozen=True, slots=True)
class TrackedFile:
    path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class DirectoryState:
    path: str
    sha256: str
    file_count: int


@dataclass(frozen=True, slots=True)
class SourceState:
    schema: str
    project_uuid: str
    project_name: str
    version: int
    reason: str
    scanner: dict[str, object]
    files: dict[str, TrackedFile]
    directories: dict[str, DirectoryState]


@dataclass(frozen=True, slots=True)
class ChangedFile:
    path: str
    change: str
    old_sha256: str | None = None
    new_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class PossibleRename:
    old_path: str
    new_path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class ImpactedRecord:
    id: str
    type: str
    title: str
    status: str
    section: str
    path: str
    matched_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ChangeSet:
    baseline_exists: bool
    baseline_version: int | None
    baseline_reason: str | None
    current_version: int
    scanner_used: str
    file_count: int
    changed_files: tuple[ChangedFile, ...]
    possible_renames: tuple[PossibleRename, ...]
    impacted_records: tuple[ImpactedRecord, ...]
    impacted_sections: tuple[str, ...]
    unlinked_changed_files: tuple[str, ...]
    unbaselined_files: tuple[str, ...] = ()


def scan_workspace(
    paths: ProjectPaths,
    config: ProjectConfig,
    *,
    reason: str = "manual",
    version: int = 1,
) -> SourceState:
    scanner_used, candidates = _scan_candidate_paths(paths, config)
    files: dict[str, TrackedFile] = {}
    for file_path in candidates:
        if not file_path.is_file():
            continue
        if _should_skip_path(file_path, paths, config):
            continue
        relative_path = _relative_posix_path(paths.workspace_root, file_path)
        if not _matches_any_pattern(relative_path, config.tracking_include):
            continue
        if _matches_any_pattern(relative_path, config.tracking_exclude):
            continue
        size = file_path.stat().st_size
        if size > config.tracking_max_file_bytes:
            continue
        files[relative_path] = TrackedFile(
            path=relative_path,
            sha256=_sha256_for_path(file_path),
        )
    sorted_files = dict(sorted(files.items()))
    return SourceState(
        schema=SOURCE_STATE_SCHEMA,
        project_uuid=config.project_uuid,
        project_name=config.project_name,
        version=version,
        reason=reason,
        scanner={
            "mode": config.tracking_scanner,
            "used": scanner_used,
            "include": list(config.tracking_include),
            "exclude": list(config.tracking_exclude),
            "max_file_bytes": config.tracking_max_file_bytes,
            "hash_algorithm": "sha256",
            "hash_content": "utf8-surrogateescape-lf-normalized",
        },
        files=sorted_files,
        directories=_build_directory_tree(sorted_files),
    )


def diff_source_states(
    baseline: SourceState | None,
    current: SourceState,
) -> ChangeSet:
    if baseline is None:
        return ChangeSet(
            baseline_exists=False,
            baseline_version=None,
            baseline_reason=None,
            current_version=current.version,
            scanner_used=_scanner_used(current),
            file_count=len(current.files),
            changed_files=(),
            possible_renames=(),
            impacted_records=(),
            impacted_sections=(),
            unlinked_changed_files=(),
            unbaselined_files=tuple(sorted(current.files)),
        )

    old_paths = set(baseline.files)
    new_paths = set(current.files)
    added_paths = sorted(new_paths - old_paths)
    deleted_paths = sorted(old_paths - new_paths)
    common_paths = sorted(old_paths & new_paths)

    changed_files: list[ChangedFile] = []
    for path in added_paths:
        tracked = current.files[path]
        changed_files.append(
            ChangedFile(
                path=path,
                change="added",
                new_sha256=tracked.sha256,
            )
        )
    for path in common_paths:
        old_tracked = baseline.files[path]
        new_tracked = current.files[path]
        if old_tracked.sha256 == new_tracked.sha256:
            continue
        changed_files.append(
            ChangedFile(
                path=path,
                change="modified",
                old_sha256=old_tracked.sha256,
                new_sha256=new_tracked.sha256,
            )
        )
    for path in deleted_paths:
        tracked = baseline.files[path]
        changed_files.append(
            ChangedFile(
                path=path,
                change="deleted",
                old_sha256=tracked.sha256,
            )
        )

    deleted_by_sha: dict[str, list[str]] = {}
    for path in deleted_paths:
        deleted_by_sha.setdefault(baseline.files[path].sha256, []).append(path)
    for sha256_paths in deleted_by_sha.values():
        sha256_paths.sort()

    possible_renames: list[PossibleRename] = []
    for path in added_paths:
        tracked = current.files[path]
        old_paths_for_sha = deleted_by_sha.get(tracked.sha256, [])
        if not old_paths_for_sha:
            continue
        old_path = old_paths_for_sha.pop(0)
        possible_renames.append(
            PossibleRename(
                old_path=old_path,
                new_path=path,
                sha256=tracked.sha256,
            )
        )

    return ChangeSet(
        baseline_exists=True,
        baseline_version=baseline.version,
        baseline_reason=baseline.reason,
        current_version=current.version,
        scanner_used=_scanner_used(current),
        file_count=len(current.files),
        changed_files=tuple(
            sorted(changed_files, key=lambda item: (item.change, item.path))
        ),
        possible_renames=tuple(
            sorted(possible_renames, key=lambda item: (item.old_path, item.new_path))
        ),
        impacted_records=(),
        impacted_sections=(),
        unlinked_changed_files=(),
    )


def resolve_impacts(
    records: list[ArchitectureRecord],
    changes: ChangeSet,
    *,
    include_draft: bool,
    include_superseded: bool,
) -> ChangeSet:
    changed_paths = {
        item.path
        for item in changes.changed_files
        if item.change in {"added", "modified", "deleted"}
    }
    impacted_records: list[ImpactedRecord] = []
    impacted_sections: set[str] = set(changes.impacted_sections)
    linked_changed_paths: set[str] = set()
    for record in records:
        if record.type != "section" and not is_visible_status(
            record.status,
            include_draft=include_draft,
            include_superseded=include_superseded,
        ):
            continue
        matched_refs = sorted(
            {
                source_ref.path
                for source_ref in record.source_refs
                for changed_path in changed_paths
                if _source_ref_matches_path(source_ref.path, changed_path)
            }
        )
        if not matched_refs:
            continue
        linked_changed_paths.update(
            changed_path
            for changed_path in changed_paths
            if any(
                _source_ref_matches_path(source_ref.path, changed_path)
                for source_ref in record.source_refs
            )
        )
        if record.type == "section":
            impacted_sections.add(record.section)
            continue
        impacted_records.append(
            ImpactedRecord(
                id=record.id,
                type=record.type,
                title=record.title,
                status=record.status,
                section=record.section,
                path=record.path.as_posix(),
                matched_refs=tuple(matched_refs),
            )
        )
        impacted_sections.add(record.section)
    return ChangeSet(
        baseline_exists=changes.baseline_exists,
        baseline_version=changes.baseline_version,
        baseline_reason=changes.baseline_reason,
        current_version=changes.current_version,
        scanner_used=changes.scanner_used,
        file_count=changes.file_count,
        changed_files=changes.changed_files,
        possible_renames=changes.possible_renames,
        impacted_records=tuple(sorted(impacted_records, key=lambda item: item.id)),
        impacted_sections=tuple(sorted(impacted_sections)),
        unlinked_changed_files=tuple(sorted(changed_paths - linked_changed_paths)),
        unbaselined_files=changes.unbaselined_files,
    )


def _scan_candidate_paths(
    paths: ProjectPaths,
    config: ProjectConfig,
) -> tuple[str, list[Path]]:
    scanner_mode = config.tracking_scanner
    if scanner_mode == "filesystem":
        return ("filesystem", _scan_filesystem_paths(paths.workspace_root))
    if scanner_mode == "git":
        return ("git", _scan_git_paths(paths.workspace_root))
    try:
        return ("git", _scan_git_paths(paths.workspace_root))
    except StorageError:
        return ("filesystem", _scan_filesystem_paths(paths.workspace_root))


def _scan_git_paths(workspace_root: Path) -> list[Path]:
    if shutil.which("git") is None:
        raise StorageError("git is not available for source tracking.")
    result = subprocess.run(
        [
            "git",
            "-C",
            str(workspace_root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise StorageError("git scanner could not enumerate workspace files.")
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        relative_path = line.strip()
        if not relative_path:
            continue
        paths.append((workspace_root / Path(relative_path)).resolve())
    return sorted(paths)


def _scan_filesystem_paths(workspace_root: Path) -> list[Path]:
    return sorted(
        path.resolve() for path in workspace_root.rglob("*") if path.is_file()
    )


def _should_skip_path(
    path: Path,
    paths: ProjectPaths,
    config: ProjectConfig,
) -> bool:
    resolved = path.resolve()
    if _is_relative_to(resolved, paths.config_root):
        return True
    if _is_relative_to(resolved, paths.archledger_dir):
        return True
    if paths.build_dir != paths.workspace_root and _is_relative_to(
        resolved, paths.build_dir
    ):
        return True
    if resolved in _generated_output_paths(paths, config):
        return True
    return False


def _relative_posix_path(workspace_root: Path, path: Path) -> str:
    return path.relative_to(workspace_root).as_posix()


def _sha256_for_path(path: Path) -> str:
    data = path.read_bytes()
    text = data.decode("utf-8", errors="surrogateescape")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(
        normalized.encode("utf-8", errors="surrogateescape")
    ).hexdigest()


def scan_git_revision(
    paths: ProjectPaths,
    config: ProjectConfig,
    revision: str,
    *,
    reason: str,
    version: int = 0,
) -> SourceState:
    """Build a SourceState from a git revision using ls-tree and show."""
    workspace = str(paths.workspace_root)
    # Get file list at revision
    result = subprocess.run(
        ["git", "-C", workspace, "ls-tree", "-r", "--name-only", revision],
        capture_output=True,
        text=True,
        check=True,
    )
    files: dict[str, TrackedFile] = {}
    for line in result.stdout.splitlines():
        relative_path = line.strip()
        if not relative_path:
            continue
        if not _matches_any_pattern(relative_path, config.tracking_include):
            continue
        if _matches_any_pattern(relative_path, config.tracking_exclude):
            continue
        if _should_skip_path(paths.workspace_root / relative_path, paths, config):
            continue
        try:
            content_result = subprocess.run(
                ["git", "-C", workspace, "show", f"{revision}:{relative_path}"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            continue
        text = content_result.stdout.decode("utf-8", errors="surrogateescape")
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        sha = hashlib.sha256(
            normalized.encode("utf-8", errors="surrogateescape")
        ).hexdigest()
        files[relative_path] = TrackedFile(path=relative_path, sha256=sha)
    sorted_files = dict(sorted(files.items()))
    return SourceState(
        schema=SOURCE_STATE_SCHEMA,
        project_uuid=config.project_uuid,
        project_name=config.project_name,
        version=version,
        reason=reason,
        scanner={"mode": "git", "used": "git", "revision": revision},
        files=sorted_files,
        directories=_build_directory_tree(sorted_files),
    )


def scan_since_merge_base(
    paths: ProjectPaths,
    config: ProjectConfig,
    revision: str,
    *,
    reason: str = "merge-base",
) -> tuple[SourceState, SourceState]:
    """Return (base_state, current_state) for merge-base comparison."""
    workspace = str(paths.workspace_root)
    base_result = subprocess.run(
        ["git", "-C", workspace, "merge-base", "HEAD", revision],
        capture_output=True,
        text=True,
        check=True,
    )
    merge_base = base_result.stdout.strip()
    base_state = scan_git_revision(
        paths, config, merge_base, reason=f"merge-base:{merge_base[:8]}"
    )
    current_state = scan_workspace(paths, config, reason=reason)
    return base_state, current_state


def _matches_any_pattern(path: str, patterns: tuple[str, ...]) -> bool:
    return any(_matches_pattern(path, pattern) for pattern in patterns)


def _matches_pattern(path: str, pattern: str) -> bool:
    pure_path = PurePosixPath(path)
    if pure_path.match(pattern):
        return True
    if pattern.startswith("**/") and pure_path.match(pattern[3:]):
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(f"{prefix}/")
    return fnmatch(path, pattern)


def _scanner_used(state: SourceState) -> str:
    scanner_used = state.scanner.get("used")
    if not isinstance(scanner_used, str):
        return "filesystem"
    return scanner_used


def _source_ref_matches_path(source_ref_path: str, changed_path: str) -> bool:
    if source_ref_path.endswith("/"):
        return changed_path.startswith(source_ref_path)
    return source_ref_path == changed_path


def _generated_output_paths(paths: ProjectPaths, config: ProjectConfig) -> set[Path]:
    output_paths = {
        (paths.build_dir / config.build_default_output).resolve(),
    }
    for output_format in VALID_OUTPUT_FORMATS:
        output_paths.add(
            (
                paths.build_dir
                / default_document_filename_for_output_format(output_format)
            ).resolve()
        )
    return output_paths


def _build_directory_tree(files: dict[str, TrackedFile]) -> dict[str, DirectoryState]:
    children: dict[str, set[tuple[str, str, str]]] = {".": set()}
    file_counts: dict[str, int] = {".": 0}
    directories: set[str] = {"."}
    for file_path, tracked in sorted(files.items()):
        parts = PurePosixPath(file_path).parts
        if not parts:
            continue
        parent = "."
        ancestors = ["."]
        for part in parts[:-1]:
            child_path = part if parent == "." else f"{parent}/{part}"
            children.setdefault(parent, set()).add(("D", part, child_path))
            children.setdefault(child_path, set())
            directories.add(child_path)
            parent = child_path
            ancestors.append(parent)
        children.setdefault(parent, set()).add(("F", parts[-1], tracked.sha256))
        for directory in ancestors:
            file_counts[directory] = file_counts.get(directory, 0) + 1

    hashes: dict[str, str] = {}
    for directory in sorted(
        directories,
        key=lambda value: 0 if value == "." else len(PurePosixPath(value).parts),
        reverse=True,
    ):
        digest = hashlib.sha256()
        for kind, name, value in sorted(children.get(directory, set())):
            if kind == "D":
                value = hashes[value]
            digest.update(f"{kind}\0{name}\0{value}\n".encode())
        hashes[directory] = digest.hexdigest()

    return {
        path: DirectoryState(
            path=path,
            sha256=hashes[path],
            file_count=file_counts.get(path, 0),
        )
        for path in sorted(directories)
    }
