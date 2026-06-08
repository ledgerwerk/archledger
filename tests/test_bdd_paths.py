"""Tests for archledger.bdd.paths — BDD path conventions."""

from __future__ import annotations

from archledger.bdd.paths import (
    DEPRECATED_BDD_FEATURE_PATH_PREFIXES,
    RECOMMENDED_BDD_FEATURE_PATH,
    deprecated_bdd_feature_path_message,
    is_deprecated_bdd_feature_path,
)


class TestIsDeprecatedBddFeaturePath:
    """@bdd-paths-deprecated-*"""

    def test_tests_bdd_features_is_deprecated(self) -> None:
        assert is_deprecated_bdd_feature_path(
            "tests/bdd/features/task-mgmt/lifecycle.feature"
        )

    def test_tests_behavior_features_is_deprecated(self) -> None:
        assert is_deprecated_bdd_feature_path(
            "tests/behavior/features/task-mgmt/lifecycle.feature"
        )

    def test_specs_bdd_features_is_deprecated(self) -> None:
        assert is_deprecated_bdd_feature_path(
            "specs/bdd/features/task-mgmt/lifecycle.feature"
        )

    def test_specs_behavior_features_is_not_deprecated(self) -> None:
        assert not is_deprecated_bdd_feature_path(
            "specs/behavior/features/task-mgmt/lifecycle.feature"
        )

    def test_arbitrary_path_is_not_deprecated(self) -> None:
        assert not is_deprecated_bdd_feature_path("some/other/path.feature")

    def test_empty_string_is_not_deprecated(self) -> None:
        assert not is_deprecated_bdd_feature_path("")


class TestDeprecatedBddFeaturePathMessage:
    """@bdd-paths-deprecation-message"""

    def test_message_mentions_deprecated(self) -> None:
        msg = deprecated_bdd_feature_path_message("tests/bdd/features/x.feature")
        assert "deprecated" in msg

    def test_message_includes_recommended_path(self) -> None:
        msg = deprecated_bdd_feature_path_message("tests/bdd/features/x.feature")
        assert RECOMMENDED_BDD_FEATURE_PATH in msg

    def test_message_includes_original_path(self) -> None:
        msg = deprecated_bdd_feature_path_message("tests/bdd/features/x.feature")
        assert "tests/bdd/features/x.feature" in msg


class TestDeprecatedPrefixes:
    """Sanity check on the constant."""

    def test_prefixes_are_non_empty(self) -> None:
        assert len(DEPRECATED_BDD_FEATURE_PATH_PREFIXES) >= 3
        for prefix in DEPRECATED_BDD_FEATURE_PATH_PREFIXES:
            assert prefix.endswith("/")

    def test_recommended_path_is_under_specs_behavior(self) -> None:
        assert RECOMMENDED_BDD_FEATURE_PATH.startswith("specs/behavior/features/")
