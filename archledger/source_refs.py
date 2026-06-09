from __future__ import annotations

from pathlib import Path, PurePosixPath

from archledger.model import VALID_SOURCE_REF_ROLES, SourceRef


class RelativePosixPathError(ValueError):
    def __init__(self, *, field_name: str, kind: str) -> None:
        self.field_name = field_name
        self.kind = kind
        message = {
            "posix": f"{field_name} must use POSIX separators.",
            "relative": f"{field_name} must be relative.",
            "dotdot": f"{field_name} must not contain '..'.",
            "empty": f"{field_name} must not be empty.",
        }[kind]
        super().__init__(message)


def validate_relative_posix_path(value: str, *, field_name: str) -> str:
    # Normalize backslashes to forward slashes (Windows compatibility)
    value = value.replace("\\", "/")

    stripped = value.strip()
    if not stripped:
        raise RelativePosixPathError(field_name=field_name, kind="relative")

    pure_path = PurePosixPath(stripped)
    if pure_path.is_absolute():
        raise RelativePosixPathError(field_name=field_name, kind="relative")
    if ".." in pure_path.parts:
        raise RelativePosixPathError(field_name=field_name, kind="dotdot")

    normalized = pure_path.as_posix()
    if normalized in {"", "."}:
        raise RelativePosixPathError(field_name=field_name, kind="empty")
    return normalized


def normalize_source_refs(
    record_id: str,
    value: object,
    *,
    workspace_root: Path,
    require_exists: bool = True,
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
            require_exists=require_exists,
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
    require_exists: bool = True,
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
            require_exists=require_exists,
        )

    if not isinstance(entry, dict):
        return (
            None,
            [
                f"Record {record_id} source_refs entry {index} "
                "must be a string or mapping."
            ],
        )

    raw_path = entry.get("path")
    raw_symbols = entry.get("symbols", ())
    raw_reason = entry.get("reason", "")
    raw_role = entry.get("role", "")
    if not isinstance(raw_symbols, list) and not isinstance(raw_symbols, tuple):
        return (
            None,
            [
                f"Record {record_id} source_refs entry {index} "
                "symbols must be a list of strings."
            ],
        )
    symbol_list: list[str] = []
    for symbol in raw_symbols:
        if not isinstance(symbol, str) or not symbol.strip():
            return (
                None,
                [
                    f"Record {record_id} source_refs entry {index} "
                    "symbols must contain only non-empty strings."
                ],
            )
        symbol_list.append(symbol.strip())
    if not isinstance(raw_reason, str):
        return (
            None,
            [f"Record {record_id} source_refs entry {index} reason must be a string."],
        )
    if not isinstance(raw_role, str):
        return (
            None,
            [f"Record {record_id} source_refs entry {index} role must be a string."],
        )
    role = raw_role.strip()
    if role and role not in VALID_SOURCE_REF_ROLES:
        # Invalid role is a warning (normal check) or error (sdd check).
        # Return the role as-is for now; sdd.py will validate.
        pass
    return _build_source_ref(
        record_id,
        raw_path,
        tuple(symbol_list),
        raw_reason.strip(),
        role,
        index=index,
        workspace_root=workspace_root,
        require_exists=require_exists,
    )


def _build_source_ref(
    record_id: str,
    raw_path: object,
    symbols: tuple[str, ...],
    reason: str,
    role: str = "",
    *,
    index: int,
    workspace_root: Path,
    require_exists: bool = True,
) -> tuple[SourceRef | None, list[str]]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return (
            None,
            [
                f"Record {record_id} source_refs entry {index} "
                "must define a non-empty path."
            ],
        )
    original_path = raw_path.strip()
    is_directory_ref = original_path.endswith("/")
    path_text = original_path.rstrip("/") if is_directory_ref else original_path
    try:
        normalized_path = validate_relative_posix_path(
            path_text,
            field_name=f"Record {record_id} source_refs entry {index} path",
        )
    except RelativePosixPathError as exc:
        return None, [
            _format_source_ref_path_error(record_id, index, original_path, exc)
        ]

    if require_exists:
        absolute_ref = workspace_root / Path(normalized_path)
        if is_directory_ref:
            if not absolute_ref.is_dir():
                return (
                    None,
                    [
                        f"Record {record_id} source_refs entry {index} "
                        f"directory does not exist: {normalized_path}/"
                    ],
                )
            normalized_path = f"{normalized_path}/"
        elif not absolute_ref.exists():
            return (
                None,
                [
                    f"Record {record_id} source_refs entry {index} "
                    f"path does not exist: {normalized_path}"
                ],
            )
    elif is_directory_ref:
        normalized_path = f"{normalized_path}/"
    return (
        SourceRef(path=normalized_path, symbols=symbols, reason=reason, role=role),
        [],
    )


def _format_source_ref_path_error(
    record_id: str,
    index: int,
    original_path: str,
    error: RelativePosixPathError,
) -> str:
    prefix = f"Record {record_id} source_refs entry {index} path"
    if error.kind == "posix":
        return f"{prefix} must use POSIX separators: {original_path}"
    if error.kind == "dotdot":
        return f"{prefix} must not contain '..': {original_path}"
    if error.kind == "empty":
        return f"{prefix} must not be empty."
    return f"{prefix} must be relative."
