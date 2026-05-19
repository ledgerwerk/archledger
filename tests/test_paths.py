from __future__ import annotations

from pathlib import Path

from archledger.storage.paths import resolve_project_paths


def test_relative_archledger_dir_is_relative_to_config_path(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    (workspace_root / "archledger.toml").write_text(
        "\n".join(
            [
                "config_version = 1",
                'archledger_dir = "../shared-state/demo"',
                'project_uuid = "12345678-1234-1234-1234-123456789abc"',
                'project_name = "demo"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    paths, _, warnings = resolve_project_paths(workspace_root)

    assert warnings == []
    assert paths.archledger_dir == (workspace_root / "../shared-state/demo").resolve()
