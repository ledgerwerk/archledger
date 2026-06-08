"""Tests for archledger.bdd.exporter — direct unit tests.

Covers safe_feature_filename, safe_output_file, render functions,
and render_feature_with_rules beyond what the CLI tests exercise.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from archledger.bdd.exporter import (
    _render_feature,
    render_feature_from_example,
    render_feature_with_rules,
    safe_feature_filename,
    safe_output_file,
)
from archledger.bdd.models import BddAutomation, BddExample


class TestSafeFeatureFilename:
    """@bdd-export-safe-filename, @bdd-export-safe-filename-empty"""

    def test_normal_name(self) -> None:
        result = safe_feature_filename("Task lifecycle gates", fallback="fallback")
        assert result == "task_lifecycle_gates.feature"

    def test_special_characters_collapsed(self) -> None:
        result = safe_feature_filename("A/B\\C: D! E", fallback="fb")
        assert result == "a_b_c_d_e.feature"

    def test_empty_name_uses_fallback(self) -> None:
        result = safe_feature_filename("   ", fallback="unnamed")
        assert result == "unnamed.feature"

    def test_long_name_is_truncated(self) -> None:
        name = "A" * 200
        result = safe_feature_filename(name, fallback="fb")
        assert len(result) <= 120 + len(".feature")
        assert result.endswith(".feature")

    def test_path_separators_stripped(self) -> None:
        result = safe_feature_filename("../../etc/shadow", fallback="fb")
        assert ".." not in result
        assert "/" not in result
        assert result.endswith(".feature")

    def test_dots_and_dashes_preserved(self) -> None:
        result = safe_feature_filename("my-feature.v2", fallback="fb")
        assert result == "my-feature.v2.feature"


class TestSafeOutputFile:
    """@bdd-export-safe-output-file"""

    def test_safe_relative_file(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        result = safe_output_file(tmp_path, out_dir, "test.feature")
        assert result.name == "test.feature"
        assert str(result).startswith(str(tmp_path))

    def test_empty_filename_rejected(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        with pytest.raises(ValueError, match="unsafe name"):
            safe_output_file(tmp_path, out_dir, "")

    def test_path_separator_rejected(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        with pytest.raises(ValueError, match="unsafe name"):
            safe_output_file(tmp_path, out_dir, "sub/test.feature")

    def test_dot_dot_rejected(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        with pytest.raises(ValueError, match="unsafe name"):
            safe_output_file(tmp_path, out_dir, "..")


class TestRenderFeatureFromExample:
    """Deterministic rendering for single-rule batches."""

    def test_renders_multi_scenario(self) -> None:
        examples = [
            BddExample(
                feature="F",
                rule="R",
                scenario="S1",
                given=("g1",),
                when=("w1",),
                then=("t1",),
                tags=("tag1",),
            ),
            BddExample(
                feature="F",
                rule="R",
                scenario="S2",
                given=("g2", "g3"),
                when=("w2",),
                then=("t2",),
            ),
        ]
        text = render_feature_from_example("F", "R", examples, ["id1", "id2"])
        assert "Feature: F" in text
        assert "Rule: R" in text
        assert "Scenario: S1" in text
        assert "Scenario: S2" in text
        assert "And g3" in text
        assert "# Generated from archledger records id1, id2." in text

    def test_renders_without_rule(self) -> None:
        examples = [
            BddExample(
                feature="F",
                rule="",
                scenario="S",
                given=("g",),
                when=("w",),
                then=("t",),
            ),
        ]
        text = render_feature_from_example("F", "", examples, ["id1"])
        assert "Rule:" not in text
        # Without rule, scenarios are indented with 2 spaces
        assert "  Scenario: S" in text


class TestRenderFeatureWithRules:
    """@bdd-export-all-multi-rule"""

    def test_renders_multiple_rules(self) -> None:
        rule_groups = [
            (
                "R1",
                [
                    BddExample(
                        feature="F",
                        rule="R1",
                        scenario="S1",
                        given=("g",),
                        when=("w",),
                        then=("t",),
                        tags=("area-x",),
                    ),
                ],
                ["id1"],
            ),
            (
                "R2",
                [
                    BddExample(
                        feature="F",
                        rule="R2",
                        scenario="S2",
                        given=("g2",),
                        when=("w2",),
                        then=("t2",),
                    ),
                ],
                ["id2"],
            ),
        ]
        text = render_feature_with_rules("F", rule_groups, ["id1", "id2"])
        assert "Rule: R1" in text
        assert "Rule: R2" in text
        assert "Scenario: S1" in text
        assert "Scenario: S2" in text
        assert "@area-x" in text

    def test_empty_rule_renders_without_rule_block(self) -> None:
        rule_groups = [
            (
                "",
                [
                    BddExample(
                        feature="F",
                        rule="",
                        scenario="S",
                        given=("g",),
                        when=("w",),
                        then=("t",),
                    ),
                ],
                ["id1"],
            ),
        ]
        text = render_feature_with_rules("F", rule_groups, ["id1"])
        assert "Rule:" not in text
        assert "  Scenario: S" in text


class TestRenderFeature:
    """Single-record export rendering."""

    def test_deterministic_output(self) -> None:
        example = BddExample(
            feature="F",
            rule="R",
            scenario="S",
            given=("g",),
            when=("w",),
            then=("t",),
            tags=("tag1", "tag2"),
            automation=BddAutomation(status="linked", feature_file="f.feature"),
        )
        text1 = _render_feature(example, "al_001")
        text2 = _render_feature(example, "al_001")
        assert text1 == text2
        assert "@tag1 @tag2" in text1
        assert "Feature: F" in text1
        assert "Rule: R" in text1
        assert "Scenario: S" in text1
        assert "Given g" in text1
        assert "When w" in text1
        assert "Then t" in text1
        assert "# Generated from archledger record al_001." in text1

    def test_without_rule(self) -> None:
        example = BddExample(
            feature="F",
            rule="",
            scenario="S",
            given=("g",),
            when=("w",),
            then=("t",),
        )
        text = _render_feature(example, "al_002")
        assert "Rule:" not in text
        # Without rule, scenario is indented 2 spaces
        assert "  Scenario: S" in text

    def test_without_tags(self) -> None:
        example = BddExample(
            feature="F",
            rule="",
            scenario="S",
            given=("g",),
            when=("w",),
            then=("t",),
            tags=(),
        )
        text = _render_feature(example, "al_003")
        assert "@" not in text.split("Feature:")[0]
