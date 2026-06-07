"""Normalize and validate the ``bdd`` front-matter metadata block.

``normalize_bdd_metadata(record_id, value)`` is the single entry point used
by both ``archledger check`` (warnings) and ``archledger sdd check`` (errors
via re-normalization).  It validates the structural contract documented in
README.md and docs/agent-workflow.rst:

* ``bdd`` must be a mapping when present.
* ``feature``, ``scenario`` and the ``given``/``when``/``then`` sequences are
  required for an accepted BDD scenario record (returned as warnings here;
  the SDD layer promotes them to errors where appropriate).
* ``given``/``when``/``then``/``tags``/``task_refs``/``acceptance_criteria``
  must be string lists.
* ``automation.status`` must be one of ``pending``, ``linked``, ``automated``,
  ``not_applicable``.
* ``automation.feature_file``, when present, must be a safe relative POSIX
  path.  Existence is **not** checked here (that is a workspace-root concern);
  the SDD/ref layer performs existence checks against ``source_refs``.
* ``automation.command`` must be a string.  It is never executed.

A missing/``None`` ``bdd`` block returns ``(None, [])`` (records without BDD
metadata are perfectly valid).
"""

from __future__ import annotations

from archledger.bdd.models import (
    BDD_AUTOMATION_STATUSES,
    DEFAULT_BDD_AUTOMATION_STATUS,
    BddAutomation,
    BddExample,
)
from archledger.source_refs import RelativePosixPathError, validate_relative_posix_path

#: Sequence fields that must be string lists.
_BDD_SEQUENCE_FIELDS: tuple[str, ...] = (
    "given",
    "when",
    "then",
    "tags",
    "task_refs",
    "acceptance_criteria",
)

#: Fields that must be non-empty strings for a complete BDD example.
_BDD_REQUIRED_TEXT_FIELDS: tuple[str, ...] = ("feature", "scenario")


def normalize_bdd_metadata(
    record_id: str,
    value: object,
) -> tuple[BddExample | None, list[str]]:
    """Normalize the ``bdd`` metadata for *record_id*.

    Returns ``(BddExample | None, warnings)``.  ``warnings`` are human-readable
    strings (prefixed with the record id) suitable for both ``check`` output
    and SDD finding messages.  On a hard structural failure (``bdd`` is not a
    mapping, or an automation sub-field is fundamentally malformed) the
    example is returned as ``None`` and every problem is reported.
    """
    if value is None:
        return None, []

    if not isinstance(value, dict):
        return None, [f"Record {record_id} bdd metadata must be a mapping."]

    warnings: list[str] = []

    feature = _text_field(value, "feature", record_id, warnings)
    rule = _text_field(value, "rule", record_id, warnings, required=False)
    scenario = _text_field(value, "scenario", record_id, warnings)

    sequences = {
        field: _sequence_field(value, field, record_id, warnings)
        for field in _BDD_SEQUENCE_FIELDS
    }
    automation, automation_fatal = _normalize_automation(record_id, value, warnings)

    # A present-but-empty required text/sequence field is recoverable: keep the
    # example (so SDD can emit shape/GWT errors) but only when there is no hard
    # automation structural failure.
    example: BddExample | None
    if automation_fatal:
        example = None
    else:
        example = BddExample(
            feature=feature,
            rule=rule,
            scenario=scenario,
            given=sequences["given"],
            when=sequences["when"],
            then=sequences["then"],
            tags=sequences["tags"],
            task_refs=sequences["task_refs"],
            acceptance_criteria=sequences["acceptance_criteria"],
            automation=automation,
        )
    return example, warnings


def _text_field(
    value: dict[str, object],
    field: str,
    record_id: str,
    warnings: list[str],
    *,
    required: bool = True,
) -> str:
    raw = value.get(field)
    if raw is None:
        if required:
            warnings.append(f"Record {record_id} bdd.{field} is missing.")
        return ""
    if not isinstance(raw, str):
        warnings.append(f"Record {record_id} bdd.{field} must be a string.")
        return ""
    text = raw.strip()
    if required and not text:
        warnings.append(f"Record {record_id} bdd.{field} is empty.")
    return text


def _sequence_field(
    value: dict[str, object],
    field: str,
    record_id: str,
    warnings: list[str],
) -> tuple[str, ...]:
    raw = value.get(field)
    if raw is None:
        return ()
    if not isinstance(raw, (list, tuple)):
        warnings.append(f"Record {record_id} bdd.{field} must be a list of strings.")
        return ()
    items: list[str] = []
    for index, entry in enumerate(raw, start=1):
        if not isinstance(entry, str) or not entry.strip():
            warnings.append(
                f"Record {record_id} bdd.{field} entry {index} "
                "must be a non-empty string."
            )
            continue
        items.append(entry.strip())
    return tuple(items)


def _normalize_automation(
    record_id: str,
    value: dict[str, object],
    warnings: list[str],
) -> tuple[BddAutomation | None, bool]:
    """Return ``(automation_or_none, fatal)``.

    ``fatal`` is True only when the automation block is present but not a
    mapping — in that case the parent example cannot be safely represented.
    """
    raw = value.get("automation")
    if raw is None:
        return None, False
    if not isinstance(raw, dict):
        warnings.append(f"Record {record_id} bdd.automation must be a mapping.")
        return None, True

    status = _automation_status(record_id, raw, warnings)
    feature_file = _automation_feature_file(record_id, raw, warnings)
    scenario = _automation_text(record_id, raw, "scenario", warnings)
    command = _automation_text(record_id, raw, "command", warnings)

    automation = BddAutomation(
        status=status,
        feature_file=feature_file,
        scenario=scenario,
        command=command,
    )
    return automation, False


def _automation_status(
    record_id: str,
    raw: dict[str, object],
    warnings: list[str],
) -> str:
    value = raw.get("status", DEFAULT_BDD_AUTOMATION_STATUS)
    if not isinstance(value, str) or not value.strip():
        warnings.append(
            f"Record {record_id} bdd.automation.status must be a non-empty "
            f"string; defaulting to {DEFAULT_BDD_AUTOMATION_STATUS!r}."
        )
        return DEFAULT_BDD_AUTOMATION_STATUS
    status = value.strip()
    if status not in BDD_AUTOMATION_STATUSES:
        warnings.append(
            f"Record {record_id} bdd.automation.status {status!r} is not one "
            f"of {sorted(BDD_AUTOMATION_STATUSES)}; "
            f"defaulting to {DEFAULT_BDD_AUTOMATION_STATUS!r}."
        )
        return DEFAULT_BDD_AUTOMATION_STATUS
    return status


def _automation_feature_file(
    record_id: str,
    raw: dict[str, object],
    warnings: list[str],
) -> str:
    value = raw.get("feature_file")
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return ""
    if not isinstance(value, str):
        warnings.append(
            f"Record {record_id} bdd.automation.feature_file must be a string."
        )
        return ""
    try:
        return validate_relative_posix_path(
            value.strip(),
            field_name=f"Record {record_id} bdd.automation.feature_file",
        )
    except RelativePosixPathError as exc:
        warnings.append(str(exc))
        return ""


def _automation_text(
    record_id: str,
    raw: dict[str, object],
    field: str,
    warnings: list[str],
) -> str:
    value = raw.get(field)
    if value is None:
        return ""
    if not isinstance(value, str):
        warnings.append(f"Record {record_id} bdd.automation.{field} must be a string.")
        return ""
    return value.strip()


__all__ = ["normalize_bdd_metadata"]
