"""Minimal Gherkin parser for archledger import.

Supports only the subset needed for ``archledger bdd import``:

* ``Feature:``
* ``Rule:``
* ``Scenario:`` and ``Example:``
* ``@`` tags (applied to the next scenario)
* ``Given``, ``When``, ``Then``, ``And``, ``But`` steps

Unsupported constructs raise :class:`UnsupportedGherkinError` with a clear
message rather than silently misreading:

* ``Background:``
* ``Scenario Outline:`` / ``Scenario Template:``
* ``Examples:`` / ``Scenarios:`` tables
* Doc strings (``\"\"\"``)
* Data tables (``|``)

The parser is intentionally small and does **not** depend on any external
Cucumber/gherkin library.
"""

from __future__ import annotations

from dataclasses import dataclass


class UnsupportedGherkinError(ValueError):
    """Raised when the parser encounters a construct it cannot handle."""

    def __init__(self, message: str, *, line: int = 0) -> None:
        super().__init__(message)
        self.line = line


class GherkinSyntaxError(ValueError):
    """Raised when the parser encounters a malformed Gherkin document."""

    def __init__(self, message: str, *, line: int = 0) -> None:
        super().__init__(message)
        self.line = line


@dataclass(frozen=True, slots=True)
class ParsedStep:
    """A single Given/When/Then/And/But step."""

    keyword: str  # "Given", "When", "Then", "And", "But"
    text: str


@dataclass(frozen=True, slots=True)
class ParsedScenario:
    """A parsed Scenario or Example.

    ``rule`` carries the Rule active at the point the scenario was flushed,
    so a feature with multiple ``Rule:`` blocks preserves the correct rule
    per scenario instead of collapsing to the last rule.
    """

    name: str
    tags: tuple[str, ...]
    given: tuple[str, ...]
    when: tuple[str, ...]
    then: tuple[str, ...]
    rule: str = ""


@dataclass(slots=True)
class ParsedFeature:
    """A parsed Feature containing optional Rule and Scenarios."""

    name: str
    rule: str = ""
    tags: tuple[str, ...] = ()
    scenarios: tuple[ParsedScenario, ...] = ()


# --- keyword constants ---
_FEATURE_KEYWORDS = ("Feature:",)
_RULE_KEYWORDS = ("Rule:",)
_SCENARIO_KEYWORDS = ("Scenario:", "Example:")
_GIVEN_KEYWORDS = ("Given",)
_WHEN_KEYWORDS = ("When",)
_THEN_KEYWORDS = ("Then",)
_STEP_KEYWORDS = ("Given", "When", "Then", "And", "But")

# Unsupported keywords that trigger a clear error.
_UNSUPPORTED_KEYWORDS = {
    "Background:",
    "Scenario Outline:",
    "Scenario Template:",
    "Examples:",
    "Scenarios:",
}

_TAG_MARKER = "@"
_DOC_STRING_MARKER = '"""'
_DATA_TABLE_MARKER = "|"


def parse_gherkin(text: str) -> ParsedFeature:
    """Parse a Gherkin text into a :class:`ParsedFeature`.

    Raises :class:`UnsupportedGherkinError` for constructs the parser cannot
    handle, and :class:`GherkinSyntaxError` for malformed documents.
    """
    lines = text.splitlines()
    feature_name = ""
    rule_name = ""
    feature_tags: list[str] = []
    pending_tags: list[str] = []
    scenarios: list[ParsedScenario] = []

    current_scenario_name: str | None = None
    current_scenario_tags: list[str] = []
    current_given: list[str] = []
    current_when: list[str] = []
    current_then: list[str] = []
    current_step_bucket: list[str] | None = None

    found_feature = False

    line_number = 0
    for raw_line in lines:
        line_number += 1
        line = raw_line.strip()

        # Skip blank lines and comments
        if not line or line.startswith("#"):
            continue

        # Doc strings -- reject
        if line == _DOC_STRING_MARKER:
            raise UnsupportedGherkinError(
                "Doc strings (triple-quoted blocks) are not supported.",
                line=line_number,
            )

        # Data tables -- reject
        if line.startswith(_DATA_TABLE_MARKER):
            raise UnsupportedGherkinError(
                "Data tables are not supported.",
                line=line_number,
            )

        # Tags
        if line.startswith(_TAG_MARKER):
            tags = _parse_tags(line, line_number)
            pending_tags.extend(tags)
            continue

        # Unsupported keywords -- reject early
        for unsupported in _UNSUPPORTED_KEYWORDS:
            if line.startswith(unsupported):
                raise UnsupportedGherkinError(
                    f"{unsupported} is not supported by the archledger",
                    line=line_number,
                )

        # Try to match a keyword-based line
        ctx = _ParseContext(
            line=line,
            line_number=line_number,
            pending_tags=pending_tags,
            found_feature=found_feature,
            current_scenario_name=current_scenario_name,
            current_scenario_tags=current_scenario_tags,
            current_given=current_given,
            current_when=current_when,
            current_then=current_then,
            current_step_bucket=current_step_bucket,
            scenarios=scenarios,
            rule_name=rule_name,
            feature_name=feature_name,
            feature_tags=feature_tags,
        )
        result = _dispatch_line(ctx)
        found_feature = result.found_feature
        feature_name = result.feature_name
        rule_name = result.rule_name
        feature_tags = result.feature_tags
        pending_tags = result.pending_tags
        current_scenario_name = result.current_scenario_name
        current_scenario_tags = result.current_scenario_tags
        current_given = result.current_given
        current_when = result.current_when
        current_then = result.current_then
        current_step_bucket = result.current_step_bucket
        scenarios = result.scenarios

    # Flush the last scenario
    _flush_scenario(
        current_scenario_name,
        current_scenario_tags,
        current_given,
        current_when,
        current_then,
        scenarios,
        rule=rule_name,
    )

    if not found_feature:
        raise GherkinSyntaxError("No Feature: line found.")

    # ParsedFeature.rule is a derived convenience: the first non-empty rule
    # among scenarios (falls back to the tracked rule_name). It is NOT the
    # authoritative per-scenario rule; use ParsedScenario.rule for that.
    feature_rule = next((s.rule for s in scenarios if s.rule), rule_name)

    return ParsedFeature(
        name=feature_name,
        rule=feature_rule,
        tags=tuple(feature_tags),
        scenarios=tuple(scenarios),
    )


def _parse_tags(line: str, line_number: int) -> list[str]:
    """Parse ``@tag1 @tag2`` into a list of tag strings (without ``@``)."""
    tags: list[str] = []
    for token in line.split():
        if not token.startswith(_TAG_MARKER):
            raise GherkinSyntaxError(
                f"Expected tag starting with '@', got {token!r}.",
                line=line_number,
            )
        tag = token[1:].strip()
        if tag:
            tags.append(tag)
    return tags


def _flush_scenario(
    name: str | None,
    tags: list[str],
    given: list[str],
    when: list[str],
    then: list[str],
    scenarios: list[ParsedScenario],
    rule: str = "",
) -> None:
    """Append the current scenario to *scenarios* if one is active.

    *rule* is the Rule active at the point the scenario is flushed, so a
    multi-rule feature preserves the correct rule per scenario.
    """
    if name is None:
        return
    scenarios.append(
        ParsedScenario(
            name=name,
            tags=tuple(tags),
            given=tuple(given),
            when=tuple(when),
            then=tuple(then),
            rule=rule,
        )
    )


@dataclass(frozen=True, slots=True)
class _ParseContext:
    """Internal mutable-state snapshot for line dispatch."""

    line: str
    line_number: int
    pending_tags: list[str]
    found_feature: bool
    current_scenario_name: str | None
    current_scenario_tags: list[str]
    current_given: list[str]
    current_when: list[str]
    current_then: list[str]
    current_step_bucket: list[str] | None
    scenarios: list[ParsedScenario]
    rule_name: str
    feature_name: str
    feature_tags: list[str]


def _dispatch_line(ctx: _ParseContext) -> _ParseContext:
    """Dispatch a single line to the appropriate keyword handler."""
    line, ln = ctx.line, ctx.line_number
    pending = ctx.pending_tags
    scenarios = ctx.scenarios

    # Feature
    for kw in _FEATURE_KEYWORDS:
        if line.startswith(kw):
            if ctx.found_feature:
                raise GherkinSyntaxError("Multiple Feature: lines found.", line=ln)
            return _replace(
                ctx,
                found_feature=True,
                feature_name=line[len(kw) :].strip(),
                feature_tags=list(pending),
                pending_tags=[],
                current_step_bucket=None,
            )

    # Rule
    for kw in _RULE_KEYWORDS:
        if line.startswith(kw):
            _flush_scenario(
                ctx.current_scenario_name,
                ctx.current_scenario_tags,
                ctx.current_given,
                ctx.current_when,
                ctx.current_then,
                scenarios,
                rule=ctx.rule_name,
            )
            return _replace(
                ctx,
                current_scenario_name=None,
                current_scenario_tags=[],
                current_given=[],
                current_when=[],
                current_then=[],
                current_step_bucket=None,
                rule_name=line[len(kw) :].strip(),
                pending_tags=[],
            )

    # Scenario / Example
    for kw in _SCENARIO_KEYWORDS:
        if line.startswith(kw):
            _flush_scenario(
                ctx.current_scenario_name,
                ctx.current_scenario_tags,
                ctx.current_given,
                ctx.current_when,
                ctx.current_then,
                scenarios,
                rule=ctx.rule_name,
            )
            return _replace(
                ctx,
                current_scenario_name=line[len(kw) :].strip(),
                current_scenario_tags=list(pending),
                current_given=[],
                current_when=[],
                current_then=[],
                current_step_bucket=None,
                pending_tags=[],
            )

    # Steps
    for kw in _STEP_KEYWORDS:
        if line.startswith(kw + " ") or line == kw:
            step_text = line[len(kw) :].strip()
            if kw in _GIVEN_KEYWORDS:
                new_given = ctx.current_given + [step_text]
                return _replace(
                    ctx,
                    current_given=new_given,
                    current_step_bucket=new_given,
                )
            elif kw in _WHEN_KEYWORDS:
                new_when = ctx.current_when + [step_text]
                return _replace(
                    ctx,
                    current_when=new_when,
                    current_step_bucket=new_when,
                )
            elif kw in _THEN_KEYWORDS:
                new_then = ctx.current_then + [step_text]
                return _replace(
                    ctx,
                    current_then=new_then,
                    current_step_bucket=new_then,
                )
            else:
                # And / But -- append to last bucket
                if ctx.current_step_bucket is None:
                    raise GherkinSyntaxError(
                        f"'{kw}' used before any Given/When/Then.",
                        line=ln,
                    )
                ctx.current_step_bucket.append(step_text)
                return ctx

    if ctx.found_feature:
        raise GherkinSyntaxError(
            f"Unrecognized line: {line!r}",
            line=ln,
        )

    return ctx


def _replace(ctx: _ParseContext, **overrides: object) -> _ParseContext:
    """Return a new _ParseContext with some fields replaced."""
    # Build a dict from the current ctx, update with overrides, construct new
    data = {
        "line": ctx.line,
        "line_number": ctx.line_number,
        "pending_tags": ctx.pending_tags,
        "found_feature": ctx.found_feature,
        "current_scenario_name": ctx.current_scenario_name,
        "current_scenario_tags": ctx.current_scenario_tags,
        "current_given": ctx.current_given,
        "current_when": ctx.current_when,
        "current_then": ctx.current_then,
        "current_step_bucket": ctx.current_step_bucket,
        "scenarios": ctx.scenarios,
        "rule_name": ctx.rule_name,
        "feature_name": ctx.feature_name,
        "feature_tags": ctx.feature_tags,
    }
    data.update(overrides)  # type: ignore[arg-type]
    return _ParseContext(**data)  # type: ignore[arg-type]


__all__ = [
    "GherkinSyntaxError",
    "ParsedFeature",
    "ParsedScenario",
    "ParsedStep",
    "UnsupportedGherkinError",
    "parse_gherkin",
]
