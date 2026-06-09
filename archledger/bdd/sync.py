"""BDD sync: compare feature files against record metadata and report drift.

``bdd sync --check`` makes the canonical-source ambiguity visible:
archledger metadata is canonical by default, but imported feature files can
temporarily be an input source. This module reports differences between the
two views without modifying either.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archledger.bdd.gherkin import (
    GherkinSyntaxError,
    ParsedFeature,
    UnsupportedGherkinError,
    parse_gherkin,
)
from archledger.bdd.normalize import normalize_bdd_metadata
from archledger.bdd.paths import (
    deprecated_bdd_feature_path_message,
    is_deprecated_bdd_feature_path,
)
from archledger.repository import ArchitectureRepository


@dataclass(frozen=True, slots=True)
class BddSyncFinding:
    """One drift finding between a feature file and record metadata."""

    code: str
    severity: str  # "warning" or "error"
    message: str
    record_id: str = ""
    feature_file: str = ""


@dataclass(frozen=True, slots=True)
class BddSyncResponse:
    schema: str = "archledger.bdd-sync.v1"
    checked: int = 0
    findings: tuple[BddSyncFinding, ...] = ()
    feature_files_checked: int = 0


@dataclass(frozen=True, slots=True)
class ParsedFeatureResult:
    feature: ParsedFeature | None
    findings: tuple[BddSyncFinding, ...] = ()


def check_bdd_sync(repo: ArchitectureRepository) -> BddSyncResponse:
    """Compare .feature files against record bdd metadata and report drift."""
    records = repo.load_all_records(include_sections=True)
    findings: list[BddSyncFinding] = []
    files_checked: set[str] = set()
    parse_cache: dict[str, ParsedFeatureResult] = {}

    # Collect all records with bdd metadata and their automation.feature_file
    bdd_records: list[
        tuple[str, dict, str, object]
    ] = []  # (id, raw_bdd, feature_file, example)
    for record in records:
        raw_bdd = record.metadata.get("bdd")
        if raw_bdd is None:
            continue
        example, warnings = normalize_bdd_metadata(record.id, raw_bdd)
        if example is None:
            findings.append(
                BddSyncFinding(
                    code="BDD-SYNC-INVALID-METADATA",
                    severity="error",
                    message=(
                        f"Record {record.id} has invalid bdd metadata: "
                        f"{'; '.join(warnings)}"
                    ),
                    record_id=record.id,
                )
            )
            continue
        auto = example.automation
        feature_file = auto.feature_file if auto else ""
        bdd_records.append((record.id, raw_bdd, feature_file, example))

    # For each record with a linked feature file, check the file exists
    # and compare scenarios
    feature_files_with_records: dict[
        str, list[tuple[str, object]]
    ] = {}  # file -> [(record_id, example)]
    for record_id, _raw_bdd, feature_file, example in bdd_records:
        if not feature_file:
            continue
        feature_files_with_records.setdefault(feature_file, []).append(
            (record_id, example)
        )
        if is_deprecated_bdd_feature_path(feature_file):
            findings.append(
                BddSyncFinding(
                    code="BDD-FEATURE-PATH-CONVENTION",
                    severity="warning",
                    message=deprecated_bdd_feature_path_message(feature_file),
                    record_id=record_id,
                    feature_file=feature_file,
                )
            )
        files_checked.add(feature_file)
        parsed = parse_cache.get(feature_file)
        if parsed is None:
            parsed = _load_feature_for_sync(
                repo,
                feature_file,
                record_id=record_id,
            )
            parse_cache[feature_file] = parsed
            findings.extend(parsed.findings)
        if parsed.feature is None:
            continue

        # Check if the scenario exists in the feature file
        scenario_names = {s.name for s in parsed.feature.scenarios}
        if example.scenario not in scenario_names:
            findings.append(
                BddSyncFinding(
                    code="BDD-SYNC-SCENARIO-MISSING",
                    severity="warning",
                    message=(
                        f"Record {record_id} bdd.scenario {example.scenario!r} "
                        f"not found in {feature_file}."
                    ),
                    record_id=record_id,
                    feature_file=feature_file,
                )
            )
            continue

        # Compare GWT steps for the matching scenario
        for s in parsed.feature.scenarios:
            if s.name != example.scenario:
                continue
            if tuple(s.given) != example.given:
                findings.append(
                    BddSyncFinding(
                        code="BDD-SYNC-GWT-MISMATCH",
                        severity="warning",
                        message=(
                            f"Record {record_id} bdd.given differs from "
                            f"{feature_file}:{example.scenario}."
                        ),
                        record_id=record_id,
                        feature_file=feature_file,
                    )
                )
            if tuple(s.when) != example.when:
                findings.append(
                    BddSyncFinding(
                        code="BDD-SYNC-GWT-MISMATCH",
                        severity="warning",
                        message=(
                            f"Record {record_id} bdd.when differs from "
                            f"{feature_file}:{example.scenario}."
                        ),
                        record_id=record_id,
                        feature_file=feature_file,
                    )
                )
            if tuple(s.then) != example.then:
                findings.append(
                    BddSyncFinding(
                        code="BDD-SYNC-GWT-MISMATCH",
                        severity="warning",
                        message=(
                            f"Record {record_id} bdd.then differs from "
                            f"{feature_file}:{example.scenario}."
                        ),
                        record_id=record_id,
                        feature_file=feature_file,
                    )
                )

    # Check for orphan feature scenarios (in file but no record)
    for feature_file, record_entries in feature_files_with_records.items():
        parsed = parse_cache.get(feature_file)
        if parsed is None:
            parsed = _load_feature_for_sync(repo, feature_file)
            parse_cache[feature_file] = parsed
            findings.extend(parsed.findings)
        if parsed.feature is None:
            continue
        record_scenarios = {e.scenario for _, e in record_entries}
        for s in parsed.feature.scenarios:
            if s.name not in record_scenarios:
                findings.append(
                    BddSyncFinding(
                        code="BDD-SYNC-ORPHAN-SCENARIO",
                        severity="warning",
                        message=(
                            f"Feature file {feature_file} has scenario "
                            f"{s.name!r} with no matching record."
                        ),
                        feature_file=feature_file,
                    )
                )

    return BddSyncResponse(
        checked=len(bdd_records),
        findings=tuple(findings),
        feature_files_checked=len(files_checked),
    )


def _load_feature_for_sync(
    repo: ArchitectureRepository,
    feature_file: str,
    *,
    record_id: str = "",
) -> ParsedFeatureResult:
    safe_path = repo.paths.workspace_root / Path(feature_file)
    if not safe_path.is_file():
        return ParsedFeatureResult(
            feature=None,
            findings=(
                BddSyncFinding(
                    code="BDD-SYNC-FILE-MISSING",
                    severity="error",
                    message=(
                        f"Record {record_id} links to {feature_file!r} which does not "
                        "exist."
                        if record_id
                        else f"Feature file {feature_file!r} does not exist."
                    ),
                    record_id=record_id,
                    feature_file=feature_file,
                ),
            ),
        )
    try:
        text = safe_path.read_text(encoding="utf-8")
    except OSError as exc:
        return ParsedFeatureResult(
            feature=None,
            findings=(
                BddSyncFinding(
                    code="BDD-SYNC-FILE-READ",
                    severity="error",
                    message=str(exc),
                    record_id=record_id,
                    feature_file=feature_file,
                ),
            ),
        )
    try:
        return ParsedFeatureResult(feature=parse_gherkin(text))
    except UnsupportedGherkinError as exc:
        return ParsedFeatureResult(
            feature=None,
            findings=(
                BddSyncFinding(
                    code="BDD-SYNC-GHERKIN-UNSUPPORTED",
                    severity="error",
                    message=str(exc),
                    record_id=record_id,
                    feature_file=feature_file,
                ),
            ),
        )
    except GherkinSyntaxError as exc:
        return ParsedFeatureResult(
            feature=None,
            findings=(
                BddSyncFinding(
                    code="BDD-SYNC-GHERKIN-SYNTAX",
                    severity="error",
                    message=str(exc),
                    record_id=record_id,
                    feature_file=feature_file,
                ),
            ),
        )


__all__ = [
    "BddSyncFinding",
    "BddSyncResponse",
    "ParsedFeatureResult",
    "check_bdd_sync",
]
