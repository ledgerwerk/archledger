from __future__ import annotations

import re
from collections.abc import Callable

from archledger.model import PLACEHOLDER_SNIPPETS, ArchitectureRecord

ALLOWED_CONSTRAINT_CATEGORIES = frozenset(
    {"technical", "organizational", "regulatory", "convention"}
)
ALLOWED_RISK_LEVELS = frozenset({"low", "medium", "high"})


def content_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    if record.type != "section":
        stripped_body = record.body.strip()
        if stripped_body and any(
            snippet in stripped_body for snippet in PLACEHOLDER_SNIPPETS
        ):
            warnings.append(f"Record body is placeholder text for {record.id}.")

    checker = _CONTENT_WARNING_CHECKERS.get(record.type)
    if checker is not None:
        warnings.extend(checker(record))
    warnings.extend(_body_syntax_warnings(record))
    return warnings


def _has_non_empty_sequence(value: object) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def _has_non_empty_text(value: object) -> bool:
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
    if _has_non_empty_text(record.metadata.get("scenario")):
        return []
    return [f"Quality goal {record.id} has no scenario."]


def _stakeholder_warnings(record: ArchitectureRecord) -> list[str]:
    if _has_non_empty_sequence(record.metadata.get("expectations")):
        return []
    return [f"Stakeholder {record.id} has no expectations."]


def _constraint_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    if not _has_non_empty_text(record.metadata.get("impact")):
        warnings.append(f"Constraint {record.id} has no impact.")
    category = record.metadata.get("category")
    if category not in ALLOWED_CONSTRAINT_CATEGORIES:
        warnings.append(f"Constraint {record.id} has unsupported category: {category}")
    return warnings


def _context_interface_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    if not _has_non_empty_text(record.metadata.get("partner")):
        warnings.append(f"Context interface {record.id} has no partner.")
    if not any(
        _has_non_empty_sequence(record.metadata.get(field))
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
    if not _has_non_empty_sequence(record.metadata.get("participants")):
        warnings.append(f"Runtime scenario {record.id} has no participants.")
    if not _has_non_empty_text(record.metadata.get("trigger")):
        warnings.append(f"Runtime scenario {record.id} has no trigger.")
    return warnings


def _infrastructure_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    environment = record.metadata.get("environment")
    if not _has_non_empty_text(environment):
        warnings.append(f"Infrastructure {record.id} has no environment.")
    if (
        isinstance(environment, str)
        and environment.strip().lower() == "production"
        and not _has_non_empty_sequence(record.metadata.get("maps_building_blocks"))
    ):
        warnings.append(
            f"Infrastructure {record.id} in production must map building "
            "blocks explicitly."
        )
    return warnings


def _adr_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    if not _contains_adr_sections(record.body):
        warnings.append(
            "ADR "
            f"{record.id} should contain Context, Decision, and Consequences "
            "sections."
        )
    if not _has_non_empty_sequence(record.metadata.get("deciders")):
        warnings.append(f"ADR {record.id} has no deciders.")
    return warnings


def _quality_scenario_warnings(record: ArchitectureRecord) -> list[str]:
    response_measure = record.metadata.get("response_measure")
    if not _has_non_empty_text(response_measure):
        return [f"Quality scenario {record.id} has no response_measure."]
    if isinstance(response_measure, str) and not _looks_measurable(response_measure):
        return [f"Quality scenario {record.id} response_measure should be measurable."]
    return []


def _risk_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    severity = record.metadata.get("severity")
    probability = record.metadata.get("probability")
    if severity not in ALLOWED_RISK_LEVELS:
        warnings.append(f"Risk {record.id} has unsupported severity: {severity}")
    if probability not in ALLOWED_RISK_LEVELS:
        warnings.append(f"Risk {record.id} has unsupported probability: {probability}")
    if not _has_non_empty_text(record.metadata.get("mitigation")):
        warnings.append(f"Risk {record.id} has no mitigation.")
    return warnings


def _glossary_term_warnings(record: ArchitectureRecord) -> list[str]:
    if _has_non_empty_text(record.metadata.get("definition")):
        return []
    return [f"Glossary term {record.id} has no definition."]


def _diagram_warnings(record: ArchitectureRecord) -> list[str]:
    warnings: list[str] = []
    diagram_type = record.metadata.get("diagram_type")
    if not isinstance(diagram_type, str) or diagram_type.strip().lower() != "mermaid":
        warnings.append(
            f"Diagram {record.id} has unsupported diagram_type: {diagram_type}"
        )
    caption = record.metadata.get("caption")
    if not isinstance(caption, str) or not caption.strip():
        warnings.append(f"Diagram {record.id} has no caption.")

    body_format_value = record.metadata.get("body_format")
    body_format = (
        body_format_value.strip().lower() if isinstance(body_format_value, str) else ""
    )
    if body_format == "markdown":
        if not _has_markdown_mermaid_block(record.body):
            warnings.append(
                f"Diagram {record.id} markdown body is missing a fenced mermaid block."
            )
        elif _markdown_mermaid_block_is_empty(record.body):
            warnings.append(f"Diagram {record.id} markdown mermaid block is empty.")
    elif body_format == "asciidoc":
        if not _has_asciidoc_mermaid_block(record.body):
            warnings.append(
                f"Diagram {record.id} asciidoc body is missing a [mermaid] block."
            )
        elif _asciidoc_mermaid_block_is_empty(record.body):
            warnings.append(f"Diagram {record.id} asciidoc mermaid block is empty.")
    return warnings


def _has_markdown_mermaid_block(body: str) -> bool:
    return bool(
        re.search(r"```mermaid\s*\n.*?\n```", body, flags=re.IGNORECASE | re.DOTALL)
    )


def _markdown_mermaid_block_is_empty(body: str) -> bool:
    match = re.search(
        r"```mermaid\s*\n(.*?)\n```",
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return False
    return not match.group(1).strip()


def _has_asciidoc_mermaid_block(body: str) -> bool:
    return bool(
        re.search(
            r"\[mermaid\]\s*\n\.\.\.\.\s*\n.*?\n\.\.\.\.",
            body,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )


def _asciidoc_mermaid_block_is_empty(body: str) -> bool:
    match = re.search(
        r"\[mermaid\]\s*\n\.\.\.\.\s*\n(.*?)\n\.\.\.\.",
        body,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return False
    return not match.group(1).strip()


def _body_syntax_warnings(record: ArchitectureRecord) -> list[str]:
    body_format_value = record.metadata.get("body_format")
    if not isinstance(body_format_value, str):
        return []
    body_format = body_format_value.strip().lower()
    if body_format == "markdown":
        if "[discrete]" in record.body and "\n===" in record.body:
            return [
                "Markdown "
                f"record {record.id} contains AsciiDoc-style discrete headings."
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
    "diagram": _diagram_warnings,
    "glossary_term": _glossary_term_warnings,
}
