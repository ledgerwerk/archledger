from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Literal

ContextFactory = Callable[["RecordContextInput"], dict[str, object]]
MetadataFieldKind = Literal[
    "string",
    "integer",
    "boolean",
    "string_list",
    "object",
    "object_list",
]


@dataclass(frozen=True, slots=True)
class RecordContextInput:
    title: str
    status: str
    section: str
    parent: str | None
    kwargs: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class MetadataFieldSpec:
    kind: MetadataFieldKind
    required: bool = False
    allowed_values: frozenset[str] | None = None
    allow_none: bool = False


@dataclass(frozen=True, slots=True)
class RecordTypeSpec:
    kind: str
    aliases: tuple[str, ...]
    directory: str
    default_section: str
    template_basename: str
    context_factory: ContextFactory
    default_status: str = "draft"
    default_level: int = 1
    metadata_fields: Mapping[str, MetadataFieldSpec] = field(default_factory=dict)


STRING_FIELD = MetadataFieldSpec("string")
OPTIONAL_STRING_FIELD = MetadataFieldSpec("string", allow_none=True)
INTEGER_FIELD = MetadataFieldSpec("integer")
STRING_LIST_FIELD = MetadataFieldSpec("string_list")
OBJECT_FIELD = MetadataFieldSpec("object")
OBJECT_LIST_FIELD = MetadataFieldSpec("object_list")

COMMON_METADATA_FIELD_SPECS: dict[str, MetadataFieldSpec] = {
    "applies_to": STRING_LIST_FIELD,
    "level": INTEGER_FIELD,
    "parent": OPTIONAL_STRING_FIELD,
}


def _string_kwarg(
    kwargs: Mapping[str, object],
    key: str,
    default: str,
) -> str:
    value = kwargs.get(key)
    return value if isinstance(value, str) else default


def _string_sequence_kwarg(
    kwargs: Mapping[str, object],
    key: str,
) -> list[str]:
    value = kwargs.get(key)
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item) for item in value if str(item).strip()]


def _requirement_context(_input: RecordContextInput) -> dict[str, object]:
    return {
        "source": "",
        "priority": "must",
        "stakeholders": [],
        "quality_goals": [],
    }


def _stakeholder_context(_input: RecordContextInput) -> dict[str, object]:
    return {"contact": "", "expectations": []}


def _quality_goal_context(_input: RecordContextInput) -> dict[str, object]:
    return {"priority": 1, "scenario": ""}


def _constraint_context(_input: RecordContextInput) -> dict[str, object]:
    return {"category": "technical", "impact": ""}


def _context_interface_context(input_data: RecordContextInput) -> dict[str, object]:
    return {
        "context_kind": _string_kwarg(
            input_data.kwargs,
            "context_kind",
            "technical",
        ),
        "partner": _string_kwarg(input_data.kwargs, "partner", ""),
        "inputs": [],
        "outputs": [],
        "channels": [],
    }


def _strategy_item_context(_input: RecordContextInput) -> dict[str, object]:
    return {"drivers": [], "constraints": [], "related_adrs": []}


def _white_box_context(_input: RecordContextInput) -> dict[str, object]:
    return {"diagram": None, "quality_characteristics": [], "tags": []}


def _black_box_context(_input: RecordContextInput) -> dict[str, object]:
    return {
        "interfaces": [],
        "location": [],
        "fulfilled_requirements": [],
        "risks": [],
        "tags": [],
    }


def _interface_context(_input: RecordContextInput) -> dict[str, object]:
    return {"providers": [], "consumers": [], "protocol": ""}


def _runtime_scenario_context(_input: RecordContextInput) -> dict[str, object]:
    return {"participants": [], "trigger": "", "result": ""}


def _infrastructure_context(input_data: RecordContextInput) -> dict[str, object]:
    return {
        "environment": _string_kwarg(
            input_data.kwargs,
            "environment",
            "development",
        ),
        "maps_building_blocks": [],
    }


def _concept_context(_input: RecordContextInput) -> dict[str, object]:
    return {"applies_to": []}


def _adr_context(_input: RecordContextInput) -> dict[str, object]:
    return {"deciders": [], "supersedes": [], "related": [], "tags": []}


def _quality_requirement_context(_input: RecordContextInput) -> dict[str, object]:
    return {
        "category": "reliability",
        "source": "",
        "measure": "",
        "scenarios": [],
    }


def _quality_scenario_context(input_data: RecordContextInput) -> dict[str, object]:
    return {
        "quality": _string_kwarg(input_data.kwargs, "quality", ""),
        "source": "",
        "stimulus": "",
        "environment": _string_kwarg(
            input_data.kwargs,
            "environment",
            "normal_development",
        ),
        "artifact": "",
        "response": "",
        "response_measure": "",
    }


def _risk_context(_input: RecordContextInput) -> dict[str, object]:
    return {
        "severity": "medium",
        "probability": "medium",
        "mitigation": "",
    }


def _glossary_term_context(input_data: RecordContextInput) -> dict[str, object]:
    return {"term": input_data.title, "definition": ""}


def _architecture_question_context(input_data: RecordContextInput) -> dict[str, object]:
    return {
        "question": input_data.title,
        "resolution_status": "open",
        "owner": "",
        "decision_due": "",
        "options": [],
        "constraints": [],
        "risks": [],
        "linked_decision": "",
    }


def _diagram_context(input_data: RecordContextInput) -> dict[str, object]:
    caption = _string_kwarg(input_data.kwargs, "caption", "")
    return {
        "diagram_type": _string_kwarg(input_data.kwargs, "diagram_type", "text"),
        "caption": caption if caption else input_data.title,
        "related_records": _string_sequence_kwarg(input_data.kwargs, "related_records"),
    }


def _acceptance_criterion_context(input_data: RecordContextInput) -> dict[str, object]:
    requirement = _string_kwarg(input_data.kwargs, "requirement", "")
    validation_command = _string_kwarg(input_data.kwargs, "validation_command", "")
    validation_expected = _string_kwarg(
        input_data.kwargs, "validation_expected", "passes"
    )
    return {
        "requirement": requirement,
        "validation": {"command": validation_command, "expected": validation_expected},
        "test_refs": [],
        "links": [],
    }


RECORD_TYPE_SPECS = (
    RecordTypeSpec(
        kind="requirement",
        aliases=("requirement",),
        directory="requirements",
        default_section="introduction_and_goals",
        template_basename="requirement",
        context_factory=_requirement_context,
        metadata_fields={
            "priority": STRING_FIELD,
            "quality_goals": STRING_LIST_FIELD,
            "source": STRING_FIELD,
            "stakeholders": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="stakeholder",
        aliases=("stakeholder",),
        directory="stakeholders",
        default_section="introduction_and_goals",
        template_basename="stakeholder",
        context_factory=_stakeholder_context,
        metadata_fields={
            "contact": STRING_FIELD,
            "expectations": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="quality_goal",
        aliases=("quality-goal", "quality_goal"),
        directory="quality_goals",
        default_section="introduction_and_goals",
        template_basename="quality_goal",
        context_factory=_quality_goal_context,
        metadata_fields={
            "priority": INTEGER_FIELD,
            "scenario": STRING_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="constraint",
        aliases=("constraint",),
        directory="constraints",
        default_section="architecture_constraints",
        template_basename="constraint",
        context_factory=_constraint_context,
        metadata_fields={
            "category": STRING_FIELD,
            "impact": STRING_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="context_interface",
        aliases=("context-interface", "context_interface"),
        directory="contexts",
        default_section="context_and_scope",
        template_basename="context_interface",
        context_factory=_context_interface_context,
        metadata_fields={
            "channels": STRING_LIST_FIELD,
            "context_kind": STRING_FIELD,
            "inputs": STRING_LIST_FIELD,
            "outputs": STRING_LIST_FIELD,
            "partner": STRING_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="strategy_item",
        aliases=("strategy-item", "strategy_item"),
        directory="strategy",
        default_section="solution_strategy",
        template_basename="strategy_item",
        context_factory=_strategy_item_context,
        metadata_fields={
            "constraints": STRING_LIST_FIELD,
            "drivers": STRING_LIST_FIELD,
            "related_adrs": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="white_box",
        aliases=("white-box", "white_box"),
        directory="building_blocks",
        default_section="building_block_view",
        template_basename="white_box",
        context_factory=_white_box_context,
        metadata_fields={
            "diagram": OPTIONAL_STRING_FIELD,
            "quality_characteristics": STRING_LIST_FIELD,
            "tags": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="black_box",
        aliases=("black-box", "black_box"),
        directory="building_blocks",
        default_section="building_block_view",
        template_basename="black_box",
        context_factory=_black_box_context,
        metadata_fields={
            "fulfilled_requirements": STRING_LIST_FIELD,
            "interfaces": STRING_LIST_FIELD,
            "location": STRING_LIST_FIELD,
            "risks": STRING_LIST_FIELD,
            "tags": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="interface",
        aliases=("interface",),
        directory="building_blocks",
        default_section="building_block_view",
        template_basename="interface",
        context_factory=_interface_context,
        metadata_fields={
            "consumers": STRING_LIST_FIELD,
            "protocol": STRING_FIELD,
            "providers": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="runtime_scenario",
        aliases=("runtime", "runtime_scenario"),
        directory="runtime",
        default_section="runtime_view",
        template_basename="runtime_scenario",
        context_factory=_runtime_scenario_context,
        metadata_fields={
            "participants": STRING_LIST_FIELD,
            "result": STRING_FIELD,
            "trigger": STRING_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="infrastructure",
        aliases=("infrastructure",),
        directory="deployment",
        default_section="deployment_view",
        template_basename="infrastructure",
        context_factory=_infrastructure_context,
        metadata_fields={
            "environment": STRING_FIELD,
            "maps_building_blocks": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="concept",
        aliases=("concept",),
        directory="concepts",
        default_section="cross_cutting_concepts",
        template_basename="concept",
        context_factory=_concept_context,
        metadata_fields={
            "applies_to": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="adr",
        aliases=("adr",),
        directory="decisions",
        default_section="architecture_decisions",
        template_basename="adr",
        context_factory=_adr_context,
        metadata_fields={
            "deciders": STRING_LIST_FIELD,
            "related": STRING_LIST_FIELD,
            "supersedes": STRING_LIST_FIELD,
            "tags": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="quality_requirement",
        aliases=("quality-requirement", "quality_requirement"),
        directory="quality_requirements",
        default_section="quality_requirements",
        template_basename="quality_requirement",
        context_factory=_quality_requirement_context,
        metadata_fields={
            "category": STRING_FIELD,
            "measure": STRING_FIELD,
            "scenarios": STRING_LIST_FIELD,
            "source": STRING_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="quality_scenario",
        aliases=("quality-scenario", "quality_scenario"),
        directory="quality_scenarios",
        default_section="quality_requirements",
        template_basename="quality_scenario",
        context_factory=_quality_scenario_context,
        metadata_fields={
            "artifact": STRING_FIELD,
            "environment": STRING_FIELD,
            "quality": STRING_FIELD,
            "response": STRING_FIELD,
            "response_measure": STRING_FIELD,
            "source": STRING_FIELD,
            "stimulus": STRING_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="risk",
        aliases=("risk",),
        directory="risks",
        default_section="risks_and_technical_debt",
        template_basename="risk",
        context_factory=_risk_context,
        metadata_fields={
            "mitigation": STRING_FIELD,
            "probability": STRING_FIELD,
            "severity": STRING_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="diagram",
        aliases=("diagram",),
        directory="diagrams",
        default_section="cross_cutting_concepts",
        template_basename="diagram",
        context_factory=_diagram_context,
        metadata_fields={
            "caption": STRING_FIELD,
            "diagram_type": STRING_FIELD,
            "related_records": STRING_LIST_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="acceptance_criterion",
        aliases=("acceptance-criterion", "acceptance_criterion", "ac"),
        directory="acceptance_criteria",
        default_section="requirements_overview",
        template_basename="acceptance_criterion",
        context_factory=_acceptance_criterion_context,
        metadata_fields={
            "requirement": STRING_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="glossary_term",
        aliases=("glossary-term", "glossary_term"),
        directory="glossary",
        default_section="glossary",
        template_basename="glossary_term",
        context_factory=_glossary_term_context,
        metadata_fields={
            "definition": STRING_FIELD,
            "term": STRING_FIELD,
        },
    ),
    RecordTypeSpec(
        kind="architecture_question",
        aliases=("architecture-question", "architecture_question", "question", "aq"),
        directory="questions",
        default_section="architecture_decisions",
        template_basename="architecture_question",
        context_factory=_architecture_question_context,
        metadata_fields={
            "constraints": STRING_LIST_FIELD,
            "decision_due": STRING_FIELD,
            "linked_decision": STRING_FIELD,
            "options": STRING_LIST_FIELD,
            "owner": STRING_FIELD,
            "question": STRING_FIELD,
            "resolution_status": STRING_FIELD,
            "risks": STRING_LIST_FIELD,
        },
    ),
)

RECORD_TYPES = {spec.kind: spec for spec in RECORD_TYPE_SPECS}
VALID_RECORD_TYPES = frozenset(RECORD_TYPES) | frozenset({"archive_tombstone"})
RECORD_TYPE_TO_DIR = {kind: spec.directory for kind, spec in RECORD_TYPES.items()}
RECORD_TYPE_TO_DEFAULT_SECTION = {
    kind: spec.default_section for kind, spec in RECORD_TYPES.items()
}
RECORD_TYPE_TO_TEMPLATE = {
    kind: f"{spec.template_basename}.md.j2" for kind, spec in RECORD_TYPES.items()
}
CLI_KIND_ALIASES = {
    alias: spec.kind for spec in RECORD_TYPE_SPECS for alias in spec.aliases
}


def metadata_field_specs_for_record_type(
    record_type: str,
) -> Mapping[str, MetadataFieldSpec]:
    spec = RECORD_TYPES.get(record_type)
    if spec is None:
        return COMMON_METADATA_FIELD_SPECS
    return {**COMMON_METADATA_FIELD_SPECS, **spec.metadata_fields}
