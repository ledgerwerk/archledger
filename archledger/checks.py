from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from archledger.model import PLACEHOLDER_SNIPPETS, ArchitectureRecord

ALLOWED_CONSTRAINT_CATEGORIES = frozenset(
    {"technical", "organizational", "regulatory", "convention"}
)
ALLOWED_RISK_LEVELS = frozenset({"low", "medium", "high"})
_ALLOWED_DIAGRAM_TYPES = frozenset({"text", "ascii", "unicode", "svgbob", "mermaid"})
_TEXT_DIAGRAM_TYPES = frozenset({"text", "ascii", "unicode"})
_MAX_TEXT_DIAGRAM_LINE_LENGTH = 120

_MARKDOWN_BLOCK_PATTERNS: dict[str, re.Pattern[str]] = {
    "mermaid": re.compile(r"```mermaid\s*\n(.*?)\n```", re.IGNORECASE | re.DOTALL),
    "svgbob": re.compile(r"```svgbob\s*\n(.*?)\n```", re.IGNORECASE | re.DOTALL),
    "text": re.compile(
        r"```(?:textdiagram|diagram|text)\s*\n(.*?)\n```", re.IGNORECASE | re.DOTALL
    ),
    "ascii": re.compile(
        r"```(?:textdiagram|diagram|ascii|text)\s*\n(.*?)\n```",
        re.IGNORECASE | re.DOTALL,
    ),
    "unicode": re.compile(
        r"```(?:textdiagram|diagram|text)\s*\n(.*?)\n```", re.IGNORECASE | re.DOTALL
    ),
}
_ASCIIDOC_BLOCK_PATTERNS: dict[str, re.Pattern[str]] = {
    "mermaid": re.compile(
        r"\[mermaid\]\s*\n\.\.\.\.\s*\n(.*?)\n\.\.\.\.",
        re.IGNORECASE | re.DOTALL,
    ),
    "svgbob": re.compile(
        r"\[svgbob\]\s*\n\.\.\.\.\s*\n(.*?)\n\.\.\.\.",
        re.IGNORECASE | re.DOTALL,
    ),
    "text": re.compile(
        r"(?:\[source,\s*text\]|\[listing\])\s*\n----\s*\n(.*?)\n----"
        r"|^\.\.\.\.\s*\n(.*?)\n\.\.\.\.",
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    ),
    "ascii": re.compile(
        r"(?:\[source,\s*(?:text|ascii)\]|\[listing\])\s*\n----\s*\n(.*?)\n----"
        r"|^\.\.\.\.\s*\n(.*?)\n\.\.\.\.",
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    ),
    "unicode": re.compile(
        r"(?:\[source,\s*text\]|\[listing\])\s*\n----\s*\n(.*?)\n----"
        r"|^\.\.\.\.\s*\n(.*?)\n\.\.\.\.",
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    ),
}


# --- Diagram syntax registry ---


@dataclass(frozen=True, slots=True)
class DiagramSyntax:
    """Describes the syntax and validation rules for one diagram type in one dialect."""

    diagram_type: str
    body_format: str  # "markdown" or "asciidoc"
    block_pattern: re.Pattern[str] | None
    label: str  # Human-readable block name for error messages
    enforce_line_width: bool = False


DIAGRAM_SYNTAX_REGISTRY: list[DiagramSyntax] = [
    # Markdown patterns
    DiagramSyntax(
        "mermaid", "markdown", _MARKDOWN_BLOCK_PATTERNS.get("mermaid"), "fenced mermaid"
    ),
    DiagramSyntax(
        "svgbob", "markdown", _MARKDOWN_BLOCK_PATTERNS.get("svgbob"), "fenced svgbob"
    ),
    DiagramSyntax(
        "text",
        "markdown",
        _MARKDOWN_BLOCK_PATTERNS.get("text"),
        "fenced text",
        enforce_line_width=True,
    ),
    DiagramSyntax(
        "ascii",
        "markdown",
        _MARKDOWN_BLOCK_PATTERNS.get("ascii"),
        "fenced ascii",
        enforce_line_width=True,
    ),
    DiagramSyntax(
        "unicode",
        "markdown",
        _MARKDOWN_BLOCK_PATTERNS.get("unicode"),
        "fenced text",
        enforce_line_width=True,
    ),
    # AsciiDoc patterns
    DiagramSyntax(
        "mermaid", "asciidoc", _ASCIIDOC_BLOCK_PATTERNS.get("mermaid"), "[mermaid]"
    ),
    DiagramSyntax(
        "svgbob", "asciidoc", _ASCIIDOC_BLOCK_PATTERNS.get("svgbob"), "[svgbob]"
    ),
    DiagramSyntax(
        "text",
        "asciidoc",
        _ASCIIDOC_BLOCK_PATTERNS.get("text"),
        "text block",
        enforce_line_width=True,
    ),
    DiagramSyntax(
        "ascii",
        "asciidoc",
        _ASCIIDOC_BLOCK_PATTERNS.get("ascii"),
        "text block",
        enforce_line_width=True,
    ),
    DiagramSyntax(
        "unicode",
        "asciidoc",
        _ASCIIDOC_BLOCK_PATTERNS.get("unicode"),
        "text block",
        enforce_line_width=True,
    ),
]


def _diagram_syntax_for(diagram_type: str, body_format: str) -> DiagramSyntax | None:
    for syntax in DIAGRAM_SYNTAX_REGISTRY:
        if syntax.diagram_type == diagram_type and syntax.body_format == body_format:
            return syntax
    return None


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
    if record.type != "section":
        warnings.extend(_bdd_warnings(record))
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
    diagram_type_raw = record.metadata.get("diagram_type")
    diagram_type = (
        diagram_type_raw.strip().lower() if isinstance(diagram_type_raw, str) else ""
    )
    if diagram_type not in _ALLOWED_DIAGRAM_TYPES:
        warnings.append(
            f"Diagram {record.id} has unsupported diagram_type: {diagram_type_raw!r}. "
            f"Allowed types: {', '.join(sorted(_ALLOWED_DIAGRAM_TYPES))}."
        )
    caption = record.metadata.get("caption")
    if not isinstance(caption, str) or not caption.strip():
        warnings.append(f"Diagram {record.id} has no caption.")

    body_format_value = record.metadata.get("body_format")
    body_format = (
        body_format_value.strip().lower() if isinstance(body_format_value, str) else ""
    )
    if body_format == "markdown":
        warnings.extend(_markdown_diagram_warnings(record, diagram_type))
    elif body_format == "asciidoc":
        warnings.extend(_asciidoc_diagram_warnings(record, diagram_type))
    return warnings


def _markdown_diagram_warnings(
    record: ArchitectureRecord, diagram_type: str
) -> list[str]:
    syntax = _diagram_syntax_for(diagram_type, "markdown")
    if syntax is None or syntax.block_pattern is None:
        return []
    return _validate_diagram_syntax(record, syntax)


def _validate_diagram_syntax(
    record: ArchitectureRecord, syntax: DiagramSyntax
) -> list[str]:
    """Validate a diagram block using a DiagramSyntax spec."""
    warnings: list[str] = []
    if syntax.block_pattern is None:
        return warnings
    match = syntax.block_pattern.search(record.body)
    if not match:
        warnings.append(
            f"Diagram {record.id} {syntax.body_format} body is missing a "
            f"{syntax.label} block."
        )
    else:
        groups = [g for g in match.groups() if g is not None]
        block_content = groups[0] if groups else ""
        if not block_content.strip():
            warnings.append(
                f"Diagram {record.id} {syntax.diagram_type} block is empty."
            )
        elif syntax.enforce_line_width:
            for line in block_content.splitlines():
                if len(line) > _MAX_TEXT_DIAGRAM_LINE_LENGTH:
                    warnings.append(
                        f"Diagram {record.id} has a text diagram line exceeding "
                        f"{_MAX_TEXT_DIAGRAM_LINE_LENGTH} characters."
                    )
                    break
    return warnings


def _asciidoc_diagram_warnings(
    record: ArchitectureRecord, diagram_type: str
) -> list[str]:
    warnings: list[str] = []
    pattern = _ASCIIDOC_BLOCK_PATTERNS.get(diagram_type)
    if pattern is None:
        return warnings
    if diagram_type == "mermaid":
        if not _has_asciidoc_mermaid_block(record.body):
            warnings.append(
                f"Diagram {record.id} asciidoc body is missing a [mermaid] block."
            )
        elif _asciidoc_mermaid_block_is_empty(record.body):
            warnings.append(f"Diagram {record.id} asciidoc mermaid block is empty.")
    elif diagram_type == "svgbob":
        match = pattern.search(record.body)
        if not match:
            warnings.append(
                f"Diagram {record.id} asciidoc body is missing a [svgbob] block."
            )
        else:
            block_content = match.group(1) or ""
            if not block_content.strip():
                warnings.append(f"Diagram {record.id} svgbob block is empty.")
    else:
        match = pattern.search(record.body)
        if not match:
            warnings.append(
                f"Diagram {record.id} asciidoc body is missing a "
                f"{diagram_type} text block."
            )
        else:
            groups = [g for g in match.groups() if g is not None]
            block_content = groups[0] if groups else ""
            if not block_content.strip():
                warnings.append(f"Diagram {record.id} {diagram_type} block is empty.")
            elif diagram_type in _TEXT_DIAGRAM_TYPES:
                for line in block_content.splitlines():
                    if len(line) > _MAX_TEXT_DIAGRAM_LINE_LENGTH:
                        warnings.append(
                            f"Diagram {record.id} has a text diagram line "
                            f"exceeding {_MAX_TEXT_DIAGRAM_LINE_LENGTH} characters."
                        )
                        break
    return warnings


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


def _bdd_warnings(record: ArchitectureRecord) -> list[str]:
    """Validate ``bdd`` front-matter metadata if present."""
    from archledger.bdd import normalize_bdd_metadata

    raw = record.metadata.get("bdd")
    if raw is None:
        return []
    _, warnings = normalize_bdd_metadata(record.id, raw)
    return warnings
