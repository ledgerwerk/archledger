"""BDD validation logic shared by ``archledger bdd validate``.

This validates BDD metadata on records and Gherkin feature files *without*
running the full SDD check. It reports structured findings (with line numbers
for parser errors) so agents can fix BDD examples before the contract gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from archledger.bdd.gherkin import (
    GherkinSyntaxError,
    ParsedFeature,
    ParsedScenario,
    UnsupportedGherkinError,
    parse_gherkin,
)
from archledger.bdd.models import BDD_AUTOMATION_STATUSES
from archledger.bdd.normalize import normalize_bdd_metadata
from archledger.repository import ArchitectureRepository
from archledger.source_refs import RelativePosixPathError, validate_relative_posix_path


@dataclass(frozen=True, slots=True)
class BddValidateFinding:
    """One validation finding for BDD metadata or a Gherkin file."""

    code: str
    severity: str  # "error" or "warning"
    message: str
    record_id: str = ""
    feature_file: str = ""
    line: int = 0


@dataclass(frozen=True, slots=True)
class BddValidateResponse:
    """Response from ``validate_bdd_*`` functions."""

    schema: str = "archledger.bdd-validate.v1"
    target: str = ""
    valid: bool = True
    findings: tuple[BddValidateFinding, ...] = ()
    scenarios: tuple[dict[str, object], ...] = field(default_factory=tuple)


def validate_bdd_record(
    repo: ArchitectureRepository,
    record_id: str,
) -> BddValidateResponse:
    """Validate a single record's ``bdd`` metadata."""
    from archledger.model import ArchitectureRecord

    record: ArchitectureRecord = repo.get_record(record_id)
    findings = _validate_record_metadata(record)
    return BddValidateResponse(
        target=f"record:{record_id}",
        valid=not any(f.severity == "error" for f in findings),
        findings=tuple(findings),
    )


def validate_bdd_all(repo: ArchitectureRepository) -> BddValidateResponse:
    """Validate ``bdd`` metadata on every record that carries it."""
    records = repo.load_all_records(include_sections=True)
    findings: list[BddValidateFinding] = []
    count = 0
    for record in records:
        if record.metadata.get("bdd") is None:
            continue
        count += 1
        findings.extend(_validate_record_metadata(record))
    return BddValidateResponse(
        target="all",
        valid=not any(f.severity == "error" for f in findings),
        findings=tuple(findings),
    )


def validate_bdd_feature_file(
    repo: ArchitectureRepository,
    feature_path: str,
) -> BddValidateResponse:
    """Validate a Gherkin feature file (parse-only, no import)."""
    workspace_root = repo.paths.workspace_root
    findings: list[BddValidateFinding] = []

    try:
        safe_path = validate_relative_posix_path(
            feature_path, field_name="Feature file"
        )
    except RelativePosixPathError as exc:
        return BddValidateResponse(
            target=f"feature-file:{feature_path}",
            valid=False,
            findings=(
                BddValidateFinding(
                    code="BDD-FEATURE-PATH",
                    severity="error",
                    message=str(exc),
                    feature_file=feature_path,
                ),
            ),
        )

    absolute_path = workspace_root / Path(safe_path)
    if not absolute_path.is_file():
        return BddValidateResponse(
            target=f"feature-file:{safe_path}",
            valid=False,
            findings=(
                BddValidateFinding(
                    code="BDD-FEATURE-MISSING",
                    severity="error",
                    message=f"Feature file does not exist: {safe_path}",
                    feature_file=safe_path,
                ),
            ),
        )

    text = absolute_path.read_text(encoding="utf-8")
    try:
        feature = parse_gherkin(text)
    except UnsupportedGherkinError as exc:
        return BddValidateResponse(
            target=f"feature-file:{safe_path}",
            valid=False,
            findings=(
                BddValidateFinding(
                    code="BDD-GHERKIN-UNSUPPORTED",
                    severity="error",
                    message=str(exc),
                    feature_file=safe_path,
                    line=getattr(exc, "line", 0),
                ),
            ),
        )
    except GherkinSyntaxError as exc:
        return BddValidateResponse(
            target=f"feature-file:{safe_path}",
            valid=False,
            findings=(
                BddValidateFinding(
                    code="BDD-GHERKIN-SYNTAX",
                    severity="error",
                    message=str(exc),
                    feature_file=safe_path,
                    line=getattr(exc, "line", 0),
                ),
            ),
        )

    findings = _validate_parsed_feature(feature, safe_path)
    scenarios = tuple(
        {
            "name": s.name,
            "rule": s.rule,
            "given": list(s.given),
            "when": list(s.when),
            "then": list(s.then),
            "tags": list(s.tags),
        }
        for s in feature.scenarios
    )
    return BddValidateResponse(
        target=f"feature-file:{safe_path}",
        valid=not any(f.severity == "error" for f in findings),
        findings=tuple(findings),
        scenarios=scenarios,
    )


# ── helpers ─────────────────────────────────────────────────────────────


def _validate_record_metadata(record: object) -> list[BddValidateFinding]:
    findings: list[BddValidateFinding] = []
    record_id = record.id
    raw_bdd = record.metadata.get("bdd")

    if raw_bdd is None:
        findings.append(
            BddValidateFinding(
                code="BDD-METADATA-ABSENT",
                severity="error",
                message=f"Record {record_id} has no bdd metadata.",
                record_id=record_id,
            )
        )
        return findings

    example, warnings = normalize_bdd_metadata(record_id, raw_bdd)
    for warning in warnings:
        findings.append(
            BddValidateFinding(
                code="BDD-METADATA-SHAPE",
                severity="error",
                message=warning,
                record_id=record_id,
            )
        )
    if example is None:
        return findings

    # GWT completeness
    missing = [
        name
        for steps, name in (
            (example.given, "given"),
            (example.when, "when"),
            (example.then, "then"),
        )
        if not steps
    ]
    if missing:
        findings.append(
            BddValidateFinding(
                code="BDD-GWT-INCOMPLETE",
                severity="error",
                message=f"Record {record_id} bdd is missing: {', '.join(missing)}.",
                record_id=record_id,
            )
        )

    # Automation status validity
    if example.automation is not None:
        status = example.automation.status
        if status not in BDD_AUTOMATION_STATUSES:
            findings.append(
                BddValidateFinding(
                    code="BDD-AUTOMATION-STATUS",
                    severity="error",
                    message=(
                        f"Record {record_id} bdd.automation.status {status!r} "
                        "is not a known status."
                    ),
                    record_id=record_id,
                )
            )
        elif status == "automated" and not (
            example.automation.command or record.test_refs
        ):
            findings.append(
                BddValidateFinding(
                    code="BDD-AUTOMATION-COMMAND",
                    severity="warning",
                    message=(
                        f"Record {record_id} bdd.automation.status=automated "
                        "but no command/test_refs are recorded."
                    ),
                    record_id=record_id,
                )
            )
        elif status == "linked" and not example.automation.feature_file:
            findings.append(
                BddValidateFinding(
                    code="BDD-AUTOMATION-LINK",
                    severity="warning",
                    message=(
                        f"Record {record_id} bdd.automation.status=linked "
                        "but feature_file is empty."
                    ),
                    record_id=record_id,
                )
            )

    # feature_file path safety
    if example.automation is not None and example.automation.feature_file:
        try:
            validate_relative_posix_path(
                example.automation.feature_file,
                field_name=f"Record {record_id} bdd.automation.feature_file",
            )
        except RelativePosixPathError as exc:
            findings.append(
                BddValidateFinding(
                    code="BDD-FEATURE-PATH",
                    severity="error",
                    message=str(exc),
                    record_id=record_id,
                    feature_file=example.automation.feature_file,
                )
            )

    # tag format: non-empty, no whitespace
    for tag in example.tags:
        if not tag or any(ch.isspace() for ch in tag):
            findings.append(
                BddValidateFinding(
                    code="BDD-TAG-FORMAT",
                    severity="warning",
                    message=(
                        f"Record {record_id} bdd tag {tag!r} is empty or "
                        "contains whitespace."
                    ),
                    record_id=record_id,
                )
            )

    return findings


def _validate_parsed_feature(
    feature: ParsedFeature,
    feature_file: str,
) -> list[BddValidateFinding]:
    findings: list[BddValidateFinding] = []
    if not feature.scenarios:
        findings.append(
            BddValidateFinding(
                code="BDD-FEATURE-NO-SCENARIOS",
                severity="warning",
                message=f"Feature file {feature_file} has no scenarios.",
                feature_file=feature_file,
            )
        )
    for scenario in feature.scenarios:
        findings.extend(_validate_parsed_scenario(scenario, feature_file))
    return findings


def _validate_parsed_scenario(
    scenario: ParsedScenario,
    feature_file: str,
) -> list[BddValidateFinding]:
    findings: list[BddValidateFinding] = []
    missing = [
        name
        for steps, name in (
            (scenario.given, "given"),
            (scenario.when, "when"),
            (scenario.then, "then"),
        )
        if not steps
    ]
    if missing:
        findings.append(
            BddValidateFinding(
                code="BDD-GWT-INCOMPLETE",
                severity="error",
                message=(
                    f"Scenario {scenario.name!r} in {feature_file} is "
                    f"missing: {', '.join(missing)}."
                ),
                feature_file=feature_file,
            )
        )
    return findings


__all__ = [
    "BddValidateFinding",
    "BddValidateResponse",
    "validate_bdd_all",
    "validate_bdd_feature_file",
    "validate_bdd_record",
]
