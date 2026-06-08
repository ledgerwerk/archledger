from __future__ import annotations

import re

_TASK_ID_RE = re.compile(r"\btask-\d{4,}\b")
_AC_ID_RE = re.compile(r"\bac-\d{4,}\b")
_BDD_ID_RE = re.compile(r"\bbdd-\d{4,}\b")
_ARCHLEDGER_ID_RE = re.compile(r"\bal_[A-Za-z0-9_]+\b")


def build_combo_trace(archledger_trace: dict[str, object]) -> dict[str, object]:
    root = archledger_trace.get("root")
    subject_id = root.get("id") if isinstance(root, dict) else None

    payload: dict[str, object] = {
        "schema": "combi.trace.v1",
        "producer": "archledger",
        "subject": {
            "type": "archledger_record",
            "id": subject_id or "",
        },
        "task_ids": [],
        "ac_ids": [],
        "bdd_ids": [],
        "archledger_refs": [],
        "source_refs": _list(archledger_trace.get("source_refs")),
        "test_refs": _list(archledger_trace.get("test_refs")),
        "evidence_refs": _list(archledger_trace.get("evidence_refs")),
        "status": {},
        "gaps": _list(archledger_trace.get("gaps")),
    }

    if isinstance(root, dict) and root.get("status") is not None:
        payload["status"] = {"archledger": root.get("status")}

    searchable = [archledger_trace]
    payload["task_ids"] = _sorted_matches(searchable, _TASK_ID_RE)
    payload["ac_ids"] = _sorted_matches(searchable, _AC_ID_RE)
    payload["bdd_ids"] = _sorted_matches(searchable, _BDD_ID_RE)
    payload["archledger_refs"] = _archledger_refs(archledger_trace, subject_id)
    return payload


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _sorted_matches(values: object, pattern: re.Pattern[str]) -> list[str]:
    return sorted(set(pattern.findall(_stringify(values))))


def _archledger_refs(trace: dict[str, object], subject_id: object) -> list[str]:
    refs = set(_ARCHLEDGER_ID_RE.findall(_stringify(trace)))
    if isinstance(subject_id, str):
        refs.discard(subject_id)
    return sorted(refs)


def _stringify(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(f"{_stringify(k)} {_stringify(v)}" for k, v in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_stringify(item) for item in value)
    return str(value)


__all__ = ["build_combo_trace"]
