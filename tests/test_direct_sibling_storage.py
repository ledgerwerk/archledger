from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.project_context import load_project_context


def test_init_uses_direct_uuid_scoped_sibling_storage(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--create-sibling-store",
            "--project-name",
            "demo",
        ],
    )

    assert result.exit_code == 0, result.output
    context = load_project_context(tmp_path)
    expected = tmp_path.parent / "ledger" / "archledger" / context.project_uuid
    assert context.data_root == expected
    assert context.mount_storage == "workspace"
    assert context.mount_scope == "project"
    assert context.mount_source == "local-provider"

    manifest = tomllib.loads((tmp_path / ".ledger" / "ledger.toml").read_text())
    mount = manifest["ledgers"]["archledger"]["mounts"]["data"]
    assert mount == {
        "storage": "workspace",
        "scope": "project",
        "path": f"archledger/{context.project_uuid}",
    }
    assert (context.data_root / ".ledger-project.toml").exists() is False
    assert (tmp_path / ".ledger" / "ledger.local.toml").is_file()
