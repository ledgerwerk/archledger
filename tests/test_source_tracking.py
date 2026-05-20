from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.repository import ArchitectureRepository
from archledger.source_tracking import (
    diff_source_states,
    resolve_impacts,
    scan_workspace,
)
from archledger.storage.paths import resolve_project_paths
from archledger.storage.source_state import read_source_state, write_source_state

runner = CliRunner()


def test_source_state_round_trip_uses_relative_paths(tmp_path: Path) -> None:
    init_project(tmp_path)
    source_path = tmp_path / "src" / "module.py"
    source_path.parent.mkdir()
    source_path.write_text("print('hello')\n", encoding="utf-8")

    paths, config, _ = resolve_project_paths(tmp_path)
    state = scan_workspace(paths, config, reason="snapshot-test")

    write_source_state(paths.source_state_path, state)
    loaded = read_source_state(paths.source_state_path)

    assert loaded is not None
    assert "src/module.py" in loaded.files
    assert all(not file_path.startswith("/") for file_path in loaded.files)


def test_diff_source_states_detects_modified_added_deleted_and_possible_renames(
    tmp_path: Path,
) -> None:
    init_project(tmp_path)
    tracked_path = tmp_path / "src" / "tracked.py"
    tracked_path.parent.mkdir()
    tracked_path.write_text("print('v1')\n", encoding="utf-8")
    renamed_from = tmp_path / "src" / "old_name.py"
    renamed_from.write_text("print('same')\n", encoding="utf-8")

    paths, config, _ = resolve_project_paths(tmp_path)
    baseline = scan_workspace(paths, config, reason="baseline")

    tracked_path.write_text("print('v2')\n", encoding="utf-8")
    renamed_from.unlink()
    (tmp_path / "src" / "new_name.py").write_text("print('same')\n", encoding="utf-8")
    (tmp_path / "src" / "added.py").write_text("print('new')\n", encoding="utf-8")

    current = scan_workspace(paths, config, reason="current")
    changes = diff_source_states(baseline, current)

    changed = {(item.change, item.path) for item in changes.changed_files}
    assert ("modified", "src/tracked.py") in changed
    assert ("deleted", "src/old_name.py") in changed
    assert ("added", "src/new_name.py") in changed
    assert ("added", "src/added.py") in changed
    assert len(changes.possible_renames) == 1
    rename = changes.possible_renames[0]
    assert rename.old_path == "src/old_name.py"
    assert rename.new_path == "src/new_name.py"
    assert rename.sha256 == current.files["src/new_name.py"].sha256


def test_diff_source_states_without_baseline_reports_unbaselined_files(
    tmp_path: Path,
) -> None:
    init_project(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("print('hello')\n", encoding="utf-8")

    paths, config, _ = resolve_project_paths(tmp_path)
    current = scan_workspace(paths, config, reason="current")
    changes = diff_source_states(None, current)

    assert changes.baseline_exists is False
    assert "src/module.py" in changes.unbaselined_files
    assert "archledger.toml" in changes.unbaselined_files


def test_scan_workspace_excludes_archledger_state_build_and_large_files(
    tmp_path: Path,
) -> None:
    init_project(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".pytest_cache" / "state.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".archledger" / "build" / "architecture.md").write_text(
        "# generated\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.md").write_text("# tracked\n", encoding="utf-8")
    (tmp_path / "large.json").write_text("x" * 2048, encoding="utf-8")

    paths, config, _ = resolve_project_paths(tmp_path)
    limited_config = replace(config, tracking_max_file_bytes=1024)
    state = scan_workspace(paths, limited_config, reason="snapshot-test")

    assert "src/module.py" in state.files
    assert "notes.md" in state.files
    assert ".pytest_cache/state.json" not in state.files
    assert ".archledger/build/architecture.md" not in state.files
    assert "large.json" not in state.files


def test_resolve_impacts_reports_linked_records_and_unlinked_files(
    tmp_path: Path,
) -> None:
    init_project(tmp_path)
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    source_file = source_dir / "module.py"
    source_file.write_text("print('v1')\n", encoding="utf-8")
    runner.invoke(
        app,
        ["--root", str(tmp_path), "new", "white-box", "--title", "Tracking layer"],
    )
    record_path = (
        tmp_path / ".archledger" / "records" / "building_blocks" / "white_box_0001.md"
    )
    record_path.write_text(
        record_path.read_text(encoding="utf-8").replace(
            "\n---\n\n",
            "\nsource_refs:\n  - src/module.py#module\n---\n\n",
            1,
        ),
        encoding="utf-8",
    )

    paths, config, _ = resolve_project_paths(tmp_path)
    repo = ArchitectureRepository(paths, config)
    baseline = scan_workspace(paths, config, reason="baseline")
    source_file.write_text("print('v2')\n", encoding="utf-8")
    (source_dir / "unlinked.py").write_text("print('unlinked')\n", encoding="utf-8")
    current = scan_workspace(paths, config, reason="current")

    changes = diff_source_states(baseline, current)
    resolved = resolve_impacts(
        repo.load_all_records(include_sections=True),
        changes,
        include_draft=True,
        include_superseded=False,
    )

    assert len(resolved.impacted_records) == 1
    impacted = resolved.impacted_records[0]
    assert impacted.id == "white_box_0001"
    assert impacted.section == "building_block_view"
    assert impacted.matched_refs == ("src/module.py",)
    assert "building_block_view" in resolved.impacted_sections
    assert resolved.unlinked_changed_files == ("src/unlinked.py",)


def init_project(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", "markdown"],
    )
    assert result.exit_code == 0
