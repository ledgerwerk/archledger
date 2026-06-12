from __future__ import annotations

from archledger.links import RecordLink, normalize_links


def test_record_link_to_existing_record_shape_is_valid() -> None:
    links, warnings = normalize_links(
        "al_0001",
        [{"rel": "documents", "target": "al_0002"}],
    )
    assert warnings == []
    assert links == (RecordLink(rel="documents", target="al_0002"),)


def test_record_link_to_missing_record_is_normalized_for_repository_warning() -> None:
    links, warnings = normalize_links(
        "al_0001",
        [{"rel": "documents", "target": "al_missing_0002"}],
    )
    assert warnings == []
    assert links[0].target_kind == "record"


def test_path_link_to_feature_file_is_accepted_without_domain_parsing() -> None:
    links, warnings = normalize_links(
        "al_0001",
        [
            {
                "rel": "documents",
                "target_kind": "path",
                "target": "specs/behavior/features/example.feature",
            }
        ],
    )
    assert warnings == []
    assert links[0].target_kind == "path"


def test_opaque_link_is_accepted() -> None:
    links, warnings = normalize_links(
        "al_0001",
        [{"rel": "relates_to", "target_kind": "opaque", "target": "external:object:1"}],
    )
    assert warnings == []
    assert links[0].target_kind == "opaque"


def test_invalid_target_kind_is_rejected() -> None:
    links, warnings = normalize_links(
        "al_0001",
        [{"rel": "documents", "target_kind": "gherkin", "target": "x.feature"}],
    )
    assert links == ()
    assert len(warnings) == 1
    assert "target_kind 'gherkin' is not supported" in warnings[0]


def test_path_target_rejects_absolute_or_parent_segments() -> None:
    links, warnings = normalize_links(
        "al_0001",
        [{"rel": "documents", "target_kind": "path", "target": "../x.feature"}],
    )
    assert links == ()
    assert len(warnings) == 1
    assert "must not contain '..'" in warnings[0]
