"""Tests for archledger scope metadata, CLI filters, and source ref handling."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from archledger.cli import app
from archledger.repository import ArchitectureRepository
from archledger.scopes import (
    RecordScope,
    normalize_scope,
    scope_matches_path,
)
from archledger.storage.paths import resolve_project_paths

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_project(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", "markdown"],
    )
    assert result.exit_code == 0, result.output


def _workspace_with_addons(tmp_path: Path) -> Path:
    _init_project(tmp_path)
    addons = tmp_path / "addons"
    for name in (
        "has_base",
        "has_email",
        "has_helpdesk",
        "has_helpdesk_crm",
    ):
        addon_dir = addons / name
        addon_dir.mkdir(parents=True)
        (addon_dir / "__manifest__.py").write_text("{}")
    (addons / "has_helpdesk" / "models").mkdir()
    (addons / "has_helpdesk" / "models" / "helpdesk_ticket.py").write_text("# ticket")
    (addons / "has_helpdesk_crm" / "models").mkdir()
    (addons / "has_helpdesk_crm" / "models" / "helpdesk_ticket.py").write_text(
        "# crm ticket"
    )
    return tmp_path


def _create_record(
    workspace: Path,
    record_id: str,
    record_type: str,
    title: str,
    *,
    status: str = "accepted",
    section: str = "architecture_decisions",
    order: int = 10,
    source_refs: list[dict[str, str]] | None = None,
    scope: dict | None = None,
) -> Path:
    paths, _, _ = resolve_project_paths(workspace)
    records_dir = paths.records_dir
    record_path = records_dir / f"{record_id}.md"

    front_matter: dict = {
        "schema_version": 2,
        "id": record_id,
        "type": record_type,
        "title": title,
        "status": status,
        "section": section,
        "order": order,
        "date": "2026-06-08",
        "body_format": "markdown",
    }
    if source_refs is not None:
        front_matter["source_refs"] = source_refs
    if scope is not None:
        front_matter["scope"] = scope

    content = (
        f"---\n{yaml.dump(front_matter, default_flow_style=False)}---\n\n{title}\n"
    )
    record_path.write_text(content)
    return record_path


def _get_repo(workspace: Path) -> ArchitectureRepository:
    from archledger.repository import ArchitectureRepository

    paths, config, _ = resolve_project_paths(workspace)
    return ArchitectureRepository(paths, config)


# ---------------------------------------------------------------------------
# 1. Scope metadata round-trip
# ---------------------------------------------------------------------------


class TestScopeRoundTrip:
    def test_normalize_and_read_back(self, tmp_path: Path) -> None:
        ws = _workspace_with_addons(tmp_path)
        scope_dict = {
            "kind": "addon_group",
            "name": "helpdesk",
            "applies_to": [
                "addons/has_helpdesk/",
                "addons/has_helpdesk_crm/",
            ],
            "excludes": [
                "addons/has_email/",
                "addons/has_base/",
            ],
            "lifecycle": "active",
        }
        scope, warnings = normalize_scope("oa_0002", scope_dict, workspace_root=ws)
        assert warnings == []
        assert scope is not None
        assert scope.kind == "addon_group"
        assert scope.name == "helpdesk"
        assert scope.applies_to == ("addons/has_helpdesk/", "addons/has_helpdesk_crm/")
        assert scope.excludes == ("addons/has_email/", "addons/has_base/")
        assert scope.lifecycle == "active"

    def test_none_scope(self) -> None:
        scope, warnings = normalize_scope("oa_0001", None)
        assert scope is None
        assert warnings == []

    def test_non_dict_scope(self) -> None:
        scope, warnings = normalize_scope("oa_0001", "bad")
        assert scope is None
        assert len(warnings) == 1

    def test_defaults(self, tmp_path: Path) -> None:
        ws = _workspace_with_addons(tmp_path)
        scope_dict = {
            "kind": "addon",
            "name": "has_helpdesk",
            "applies_to": ["addons/has_helpdesk/"],
        }
        scope, warnings = normalize_scope("oa_0001", scope_dict, workspace_root=ws)
        assert warnings == []
        assert scope is not None
        assert scope.excludes == ()
        assert scope.lifecycle == "active"


# ---------------------------------------------------------------------------
# 2. Scope path validation
# ---------------------------------------------------------------------------


class TestScopePathValidation:
    def test_accept_valid_directory(self, tmp_path: Path) -> None:
        ws = _workspace_with_addons(tmp_path)
        scope, warnings = normalize_scope(
            "oa_0001",
            {"kind": "addon", "name": "x", "applies_to": ["addons/has_helpdesk/"]},
            workspace_root=ws,
        )
        assert scope is not None
        assert warnings == []

    def test_reject_absolute_path(self, tmp_path: Path) -> None:
        scope, warnings = normalize_scope(
            "oa_0001",
            {"kind": "addon", "name": "x", "applies_to": ["/absolute/path/"]},
            workspace_root=tmp_path,
        )
        assert scope is None
        assert any("must be relative" in w for w in warnings)

    def test_reject_dotdot(self, tmp_path: Path) -> None:
        scope, warnings = normalize_scope(
            "oa_0001",
            {"kind": "addon", "name": "x", "applies_to": ["../outside/"]},
            workspace_root=tmp_path,
        )
        assert scope is None
        assert any("'..'" in w for w in warnings)

    def test_warn_missing_active_path(self, tmp_path: Path) -> None:
        scope, warnings = normalize_scope(
            "oa_0001",
            {
                "kind": "addon",
                "name": "x",
                "applies_to": ["addons/nonexistent/"],
                "lifecycle": "active",
            },
            workspace_root=tmp_path,
        )
        assert scope is not None  # still created
        assert any("does not exist" in w for w in warnings)

    def test_allow_retired_missing_path(self, tmp_path: Path) -> None:
        scope, warnings = normalize_scope(
            "oa_0001",
            {
                "kind": "addon",
                "name": "x",
                "applies_to": ["addons/nonexistent/"],
                "lifecycle": "retired",
            },
            workspace_root=tmp_path,
        )
        assert scope is not None
        assert warnings == []

    def test_invalid_kind(self) -> None:
        scope, warnings = normalize_scope(
            "oa_0001",
            {"kind": "bogus", "name": "x", "applies_to": ["foo/"]},
        )
        assert scope is None
        assert any("not allowed" in w for w in warnings)

    def test_invalid_lifecycle(self) -> None:
        scope, warnings = normalize_scope(
            "oa_0001",
            {
                "kind": "addon",
                "name": "x",
                "applies_to": ["foo/"],
                "lifecycle": "unknown",
            },
        )
        assert scope is None
        assert any("not allowed" in w for w in warnings)

    def test_empty_applies_to(self) -> None:
        scope, warnings = normalize_scope(
            "oa_0001",
            {"kind": "addon", "name": "x", "applies_to": []},
        )
        assert scope is None
        assert any("non-empty list" in w for w in warnings)

    def test_excludes_not_a_list(self) -> None:
        scope, warnings = normalize_scope(
            "oa_0001",
            {"kind": "addon", "name": "x", "applies_to": ["foo/"], "excludes": "bad"},
        )
        assert scope is None
        assert any("must be a list" in w for w in warnings)


# ---------------------------------------------------------------------------
# 3. Directory scope matching
# ---------------------------------------------------------------------------


class TestScopeDirectoryMatching:
    def _make_scope(self) -> RecordScope:
        return RecordScope(
            kind="addon_group",
            name="helpdesk",
            applies_to=("addons/has_helpdesk_crm/",),
            excludes=(),
            lifecycle="active",
        )

    def test_match_file_in_applies_to(self) -> None:
        scope = self._make_scope()
        assert scope_matches_path(
            scope, "addons/has_helpdesk_crm/models/helpdesk_ticket.py"
        )

    def test_match_directory_itself(self) -> None:
        scope = self._make_scope()
        assert scope_matches_path(scope, "addons/has_helpdesk_crm")

    def test_no_match_outside(self) -> None:
        scope = self._make_scope()
        assert not scope_matches_path(scope, "addons/has_email/models/mail.py")

    def test_no_match_unrelated(self) -> None:
        scope = self._make_scope()
        assert not scope_matches_path(scope, "other/path.py")


# ---------------------------------------------------------------------------
# 4. source_refs still drive impact (integration with context)
# ---------------------------------------------------------------------------


class TestSourceRefsImpact:
    def test_source_ref_match_in_context(self, tmp_path: Path) -> None:
        from archledger.context import build_context_for_file

        ws = _workspace_with_addons(tmp_path)
        _create_record(
            ws,
            "oa_0001",
            "adr",
            "Test ADR",
            source_refs=[{"path": "addons/has_helpdesk_crm/", "role": "implements"}],
        )

        repo = _get_repo(ws)
        result = build_context_for_file(
            repo,
            "addons/has_helpdesk_crm/models/helpdesk_ticket.py",
        )
        ids = [r["id"] for r in result.get("records", [])]
        assert "oa_0001" in ids


# ---------------------------------------------------------------------------
# 5. excludes override broad applies_to
# ---------------------------------------------------------------------------


class TestExcludesOverride:
    def test_excluded_path_not_matched(self) -> None:
        scope = RecordScope(
            kind="addon_group",
            name="all",
            applies_to=("addons/",),
            excludes=("addons/has_email/",),
            lifecycle="active",
        )
        assert scope_matches_path(scope, "addons/has_helpdesk/models/ticket.py")
        assert not scope_matches_path(scope, "addons/has_email/models/mail.py")

    def test_exclude_exact_file(self) -> None:
        scope = RecordScope(
            kind="addon",
            name="x",
            applies_to=("addons/",),
            excludes=("addons/has_email/config.py",),
            lifecycle="active",
        )
        assert not scope_matches_path(scope, "addons/has_email/config.py")
        assert scope_matches_path(scope, "addons/has_email/other.py")


# ---------------------------------------------------------------------------
# 6. Archive deleted addon (source refs relaxation)
# ---------------------------------------------------------------------------


class TestArchivedSourceRefs:
    def test_archived_missing_source_ref_no_error(self, tmp_path: Path) -> None:
        ws = _workspace_with_addons(tmp_path)
        _create_record(
            ws,
            "oa_0001",
            "adr",
            "Test ADR",
            status="archived",
            source_refs=[{"path": "addons/has_email/", "role": "implements"}],
        )
        shutil.rmtree(ws / "addons" / "has_email")

        repo = _get_repo(ws)
        records = repo.load_all_records(include_sections=False)
        assert any(r.id == "oa_0001" for r in records)

    def test_active_missing_source_ref_skipped(self, tmp_path: Path) -> None:
        """An active record with a missing source_ref gets empty refs."""
        ws = _workspace_with_addons(tmp_path)
        _create_record(
            ws,
            "oa_0002",
            "adr",
            "Active ADR",
            status="accepted",
            source_refs=[{"path": "addons/nonexistent/", "role": "implements"}],
        )

        repo = _get_repo(ws)
        records = repo.load_all_records(include_sections=False)
        record = next(r for r in records if r.id == "oa_0002")
        # The missing source ref is skipped, resulting in empty refs.
        assert record.source_refs == ()

    def test_archived_bad_path_still_fails(self, tmp_path: Path) -> None:
        scope, warnings = normalize_scope(
            "oa_0001",
            {"kind": "addon", "name": "x", "applies_to": ["../bad/"]},
            workspace_root=tmp_path,
        )
        assert scope is None


# ---------------------------------------------------------------------------
# 7. Link relationship
# ---------------------------------------------------------------------------


class TestAppliesToLink:
    def test_applies_to_link_valid(self) -> None:
        from archledger.links import VALID_LINK_RELS

        assert "applies_to" in VALID_LINK_RELS

    def test_invalid_rel_still_fails(self) -> None:
        from archledger.links import normalize_links

        links, warnings = normalize_links(
            "oa_0001", [{"rel": "bad_rel", "target": "oa_0002"}]
        )
        assert links == ()
        assert any("not an allowed relationship" in w for w in warnings)


# ---------------------------------------------------------------------------
# 8. Context scope matching integration
# ---------------------------------------------------------------------------


class TestContextScopeMatching:
    def test_context_matches_scope(self, tmp_path: Path) -> None:
        from archledger.context import build_context_for_file

        ws = _workspace_with_addons(tmp_path)
        _create_record(
            ws,
            "oa_0001",
            "building_block",
            "Helpdesk group",
            scope={
                "kind": "addon_group",
                "name": "helpdesk",
                "applies_to": [
                    "addons/has_helpdesk/",
                    "addons/has_helpdesk_crm/",
                ],
                "excludes": [],
                "lifecycle": "active",
            },
        )

        repo = _get_repo(ws)
        result = build_context_for_file(
            repo,
            "addons/has_helpdesk_crm/models/helpdesk_ticket.py",
        )
        ids = [r["id"] for r in result.get("records", [])]
        assert "oa_0001" in ids

    def test_context_excludes_scope(self, tmp_path: Path) -> None:
        from archledger.context import build_context_for_file

        ws = _workspace_with_addons(tmp_path)
        _create_record(
            ws,
            "oa_0002",
            "building_block",
            "All except email",
            scope={
                "kind": "addon_group",
                "name": "not-email",
                "applies_to": ["addons/"],
                "excludes": ["addons/has_email/"],
                "lifecycle": "active",
            },
        )

        repo = _get_repo(ws)
        result = build_context_for_file(
            repo,
            "addons/has_email/models/mail.py",
        )
        ids = [r["id"] for r in result.get("records", [])]
        assert "oa_0002" not in ids
