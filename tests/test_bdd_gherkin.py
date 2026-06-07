"""Tests for archledger.bdd.gherkin minimal Gherkin parser."""

from __future__ import annotations

import textwrap

import pytest

from archledger.bdd.gherkin import (
    GherkinSyntaxError,
    UnsupportedGherkinError,
    parse_gherkin,
)

FEATURE_TEXT = textwrap.dedent("""\
    @lifecycle @approval
    Feature: Task lifecycle gates

      Rule: Implementation requires an accepted plan

        @happy-path
        Scenario: Agent tries to implement before approval
          Given a task has a proposed plan
          And the plan has not been approved by the user
          When the agent starts implementation
          Then implementation is blocked
          And the task remains in planning or review state

        Scenario: Agent implements after approval
          Given a task has an approved plan
          When the agent starts implementation
          Then implementation proceeds normally
""")


def test_parse_feature_with_rule_and_two_scenarios() -> None:
    feature = parse_gherkin(FEATURE_TEXT)
    assert feature.name == "Task lifecycle gates"
    assert feature.rule == "Implementation requires an accepted plan"
    assert feature.tags == ("lifecycle", "approval")
    assert len(feature.scenarios) == 2
    s1, s2 = feature.scenarios
    assert s1.name == "Agent tries to implement before approval"
    assert s1.tags == ("happy-path",)
    assert s1.given == (
        "a task has a proposed plan",
        "the plan has not been approved by the user",
    )
    assert s1.when == ("the agent starts implementation",)
    assert s1.then == (
        "implementation is blocked",
        "the task remains in planning or review state",
    )
    assert s2.name == "Agent implements after approval"
    assert s2.tags == ()
    assert s2.given == ("a task has an approved plan",)
    assert s2.when == ("the agent starts implementation",)
    assert s2.then == ("implementation proceeds normally",)


def test_parse_feature_without_rule() -> None:
    text = textwrap.dedent("""\
        Feature: Simple

          Scenario: Hello
            Given X
            When Y
            Then Z
    """)
    feature = parse_gherkin(text)
    assert feature.name == "Simple"
    assert feature.rule == ""
    assert len(feature.scenarios) == 1


def test_parse_example_keyword() -> None:
    text = textwrap.dedent("""\
        Feature: Example keyword

          Example: uses Example instead of Scenario
            Given X
            When Y
            Then Z
    """)
    feature = parse_gherkin(text)
    assert len(feature.scenarios) == 1
    assert feature.scenarios[0].name == "uses Example instead of Scenario"


def test_parse_tags_on_scenarios() -> None:
    text = textwrap.dedent("""\
        Feature: Tagged

          @tag1 @tag2
          Scenario: A
            Given X
            When Y
            Then Z
    """)
    feature = parse_gherkin(text)
    assert feature.scenarios[0].tags == ("tag1", "tag2")


def test_parse_and_but_append_to_last_bucket() -> None:
    text = textwrap.dedent("""\
        Feature: Steps

          Scenario: Steps with And and But
            Given first
            And second
            When third
            But fourth
            Then fifth
            And sixth
    """)
    feature = parse_gherkin(text)
    s = feature.scenarios[0]
    assert s.given == ("first", "second")
    assert s.when == ("third", "fourth")
    assert s.then == ("fifth", "sixth")


def test_raises_on_no_feature() -> None:
    with pytest.raises(GherkinSyntaxError, match="No Feature"):
        parse_gherkin("Scenario: orphan\n  Given X\n")


def test_raises_on_multiple_features() -> None:
    text = textwrap.dedent("""\
        Feature: One
        Feature: Two
    """)
    with pytest.raises(GherkinSyntaxError, match="Multiple Feature"):
        parse_gherkin(text)


def test_raises_on_background() -> None:
    text = textwrap.dedent("""\
        Feature: BG
          Background:
            Given X
    """)
    with pytest.raises(UnsupportedGherkinError, match="Background"):
        parse_gherkin(text)


def test_raises_on_scenario_outline() -> None:
    text = textwrap.dedent("""\
        Feature: Outline
          Scenario Outline: A
            Given X
          Examples:
            | a |
    """)
    with pytest.raises(UnsupportedGherkinError, match="Scenario Outline"):
        parse_gherkin(text)


def test_raises_on_scenario_template() -> None:
    text = textwrap.dedent("""\
        Feature: Template
          Scenario Template: A
            Given X
    """)
    with pytest.raises(UnsupportedGherkinError, match="Scenario Template"):
        parse_gherkin(text)


def test_raises_on_examples_table() -> None:
    text = textwrap.dedent("""\
        Feature: Ex
          Scenario: A
            Given X
          Examples:
            | a |
    """)
    with pytest.raises(UnsupportedGherkinError, match="Examples"):
        parse_gherkin(text)


def test_raises_on_data_table() -> None:
    text = textwrap.dedent("""\
        Feature: DT
          Scenario: A
            Given X
            | col |
            | val |
    """)
    with pytest.raises(UnsupportedGherkinError, match="Data tables"):
        parse_gherkin(text)


def test_raises_on_doc_string() -> None:
    text = textwrap.dedent('''\
        Feature: DS
          Scenario: A
            Given X
            """
            hello
            """
    ''')
    with pytest.raises(UnsupportedGherkinError, match="Doc strings"):
        parse_gherkin(text)


def test_raises_on_and_before_given_when_then() -> None:
    text = textwrap.dedent("""\
        Feature: Bad
          Scenario: A
            And orphan
    """)
    with pytest.raises(GherkinSyntaxError, match="before any Given"):
        parse_gherkin(text)


def test_skips_blank_lines_and_comments() -> None:
    text = textwrap.dedent("""\
        # comment

        Feature: Comments

          # another comment

          Scenario: A
            Given X
            When Y
            Then Z
    """)
    feature = parse_gherkin(text)
    assert len(feature.scenarios) == 1


def test_parse_fixture_lifecycle_feature() -> None:
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "bdd" / "lifecycle.feature"
    if not fixture.exists():
        pytest.skip("Fixture file not present.")
    feature = parse_gherkin(fixture.read_text(encoding="utf-8"))
    assert feature.name == "Task lifecycle gates"
    assert feature.rule == "Implementation requires an accepted plan"
    assert len(feature.scenarios) == 2


def test_parse_multiple_rules_preserves_rule_per_scenario() -> None:
    """P0: multiple Rule blocks must not collapse to the last rule.

    Each scenario must capture the rule active at the point it is flushed, so
    import does not silently misassign an earlier scenario to a later rule.
    """
    text = textwrap.dedent("""\
        Feature: F

          Rule: R1
            Scenario: S1
              Given g
              When w
              Then t

          Rule: R2
            Scenario: S2
              Given g2
              When w2
              Then t2
    """)
    feature = parse_gherkin(text)
    assert len(feature.scenarios) == 2
    s1, s2 = feature.scenarios
    assert s1.name == "S1"
    assert s1.rule == "R1"
    assert s2.name == "S2"
    assert s2.rule == "R2"


def test_parsed_scenario_carries_rule_for_single_rule_feature() -> None:
    """A single-Rule feature stamps that rule on each scenario."""
    feature = parse_gherkin(FEATURE_TEXT)
    assert len(feature.scenarios) == 2
    for scenario in feature.scenarios:
        assert scenario.rule == "Implementation requires an accepted plan"
