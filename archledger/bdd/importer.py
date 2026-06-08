"""BDD importer: create archledger records from parsed Gherkin examples.

The importer creates one record per supported scenario/example using
``ArchitectureRepository.create_record()``, then patches the front matter
to add ``bdd`` metadata and a ``source_refs`` entry with role ``documents``
pointing to the originating feature file.  After mutation the record is
re-loaded and validated.

The body format (Markdown vs AsciiDoc) is determined by the project's
``config.source_format``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archledger.bdd.gherkin import ParsedFeature, ParsedScenario, parse_gherkin
from archledger.bdd.paths import (
    deprecated_bdd_feature_path_message,
    is_deprecated_bdd_feature_path,
)
from archledger.mutations import (
    add_source_ref,
    replace_record_body,
    set_record_meta,
)
from archledger.repository import ArchitectureRepository
from archledger.source_refs import validate_relative_posix_path


@dataclass(frozen=True, slots=True)
class BddImportResult:
    """Result of importing a single scenario."""

    id: str
    type: str
    title: str
    path: str


@dataclass(frozen=True, slots=True)
class BddImportResponse:
    """Top-level response from ``import_bdd_feature``."""

    schema: str = "archledger.bdd-import.v1"
    feature_file: str = ""
    created_records: tuple[BddImportResult, ...] = ()
    warnings: tuple[str, ...] = ()


def import_bdd_feature(
    repo: ArchitectureRepository,
    feature_path: str,
    *,
    kind: str,
    status: str = "proposed",
    section: str | None = None,
) -> BddImportResponse:
    """Import a Gherkin feature file into archledger.

    *feature_path* is a path relative to the workspace root (POSIX).
    *kind* must be ``runtime-scenario`` or ``quality-scenario``.
    *status* is the initial record status (default ``proposed``).
    *section* overrides the default section for the record kind.
    """
    from archledger.model import normalize_kind

    # Normalize: hyphenated kinds like "runtime-scenario" -> "runtime_scenario"
    normalized_kind = normalize_kind(kind.replace("-", "_"))
    workspace_root = repo.paths.workspace_root

    # Validate the feature file path
    safe_path = validate_relative_posix_path(
        feature_path,
        field_name="Feature file",
    )
    absolute_path = workspace_root / Path(safe_path)
    if not absolute_path.is_file():
        raise FileNotFoundError(f"Feature file does not exist: {safe_path}")

    # Parse the feature file
    text = absolute_path.read_text(encoding="utf-8")
    feature = parse_gherkin(text)

    warnings: list[str] = []
    results: list[BddImportResult] = []
    if is_deprecated_bdd_feature_path(safe_path):
        warnings.append(deprecated_bdd_feature_path_message(safe_path))

    # Use the feature-level tags as default tags for all scenarios
    feature_tags = list(feature.tags)

    for scenario in feature.scenarios:
        result = _import_scenario(
            repo=repo,
            feature=feature,
            scenario=scenario,
            normalized_kind=normalized_kind,
            feature_path=safe_path,
            feature_tags=feature_tags,
            status=status,
            section=section,
        )
        results.append(result)
        if not scenario.given or not scenario.when or not scenario.then:
            warnings.append(
                f"Scenario '{scenario.name}' is missing "
                "given/when/then steps; imported with empty sequences."
            )

    return BddImportResponse(
        feature_file=safe_path,
        created_records=tuple(results),
        warnings=tuple(warnings),
    )


def _import_scenario(
    repo: ArchitectureRepository,
    feature: ParsedFeature,
    scenario: ParsedScenario,
    normalized_kind: str,
    feature_path: str,
    feature_tags: list[str],
    status: str,
    section: str | None,
) -> BddImportResult:
    """Import a single scenario as an archledger record."""
    title = scenario.name

    # Create the record
    record = repo.create_record(
        normalized_kind,
        title,
        status=status,
        section=section,
    )

    # Build the bdd metadata block
    all_tags = list(feature_tags) + [t for t in scenario.tags if t not in feature_tags]
    bdd_metadata: dict[str, object] = {
        "feature": feature.name,
        "scenario": scenario.name,
        "tags": all_tags,
        "given": list(scenario.given),
        "when": list(scenario.when),
        "then": list(scenario.then),
        # An imported scenario is linked to its feature file by definition,
        # so automation.status defaults to 'linked' (a feature/scenario exists
        # even if executable automation is not yet wired).
        "automation": {
            "status": "linked",
            "feature_file": feature_path,
            "scenario": scenario.name,
        },
    }
    rule = getattr(scenario, "rule", "") or feature.rule
    if rule:
        bdd_metadata["rule"] = rule

    # Write bdd metadata to front matter
    set_record_meta(
        record.path,
        record.id,
        "bdd",
        bdd_metadata,
        workspace_root=repo.paths.workspace_root,
    )

    # Add source_ref for the feature file
    add_source_ref(
        record.path,
        record.id,
        feature_path,
        role="documents",
        reason="Imported Gherkin scenario source.",
        workspace_root=repo.paths.workspace_root,
    )

    # Write the BDD body content (replace, not append, so accepted imports
    # do not keep the template placeholder that would trigger SDD-PLACEHOLDER).
    body_format = record.metadata.get("body_format", "markdown")
    body_text = _generate_bdd_body(feature, scenario, body_format)
    replace_record_body(
        record.path,
        record.id,
        body_text,
        workspace_root=repo.paths.workspace_root,
    )

    # Re-load the record to verify it's valid
    reloaded = repo.get_record(record.id)

    return BddImportResult(
        id=reloaded.id,
        type=reloaded.type,
        title=reloaded.title,
        path=str(reloaded.path),
    )


def _generate_bdd_body(
    feature: ParsedFeature,
    scenario: ParsedScenario,
    body_format: str,
) -> str:
    """Generate the Markdown or AsciiDoc body for an imported BDD scenario."""
    if body_format == "asciidoc":
        return _generate_bdd_body_asciidoc(feature, scenario)
    return _generate_bdd_body_markdown(feature, scenario)


def _generate_bdd_body_markdown(
    feature: ParsedFeature,
    scenario: ParsedScenario,
) -> str:
    lines: list[str] = []
    lines.append("## Scenario")
    lines.append("")
    if feature.rule:
        lines.append(f"Rule: {feature.rule}")
        lines.append("")
    lines.append(f"Example: {scenario.name}")
    lines.append("")
    for i, step in enumerate(scenario.given):
        prefix = "Given" if i == 0 else "And"
        lines.append(f"{prefix} {step}  ")
    for i, step in enumerate(scenario.when):
        prefix = "When" if i == 0 else "And"
        lines.append(f"{prefix} {step}  ")
    for i, step in enumerate(scenario.then):
        prefix = "Then" if i == 0 else "And"
        lines.append(f"{prefix} {step}  ")
    lines.append("")
    return "\n".join(lines)


def _generate_bdd_body_asciidoc(
    feature: ParsedFeature,
    scenario: ParsedScenario,
) -> str:
    lines: list[str] = []
    lines.append("== Scenario")
    lines.append("")
    if feature.rule:
        lines.append(f"Rule: {feature.rule}")
        lines.append("")
    lines.append(f"Example: {scenario.name}")
    lines.append("")
    for i, step in enumerate(scenario.given):
        prefix = "Given" if i == 0 else "And"
        lines.append(f"{prefix} {step}")
    for i, step in enumerate(scenario.when):
        prefix = "When" if i == 0 else "And"
        lines.append(f"{prefix} {step}")
    for i, step in enumerate(scenario.then):
        prefix = "Then" if i == 0 else "And"
        lines.append(f"{prefix} {step}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "BddImportResponse",
    "BddImportResult",
    "import_bdd_feature",
]
