from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.project_context import load_project_context


def test_init_defaults_to_project_storage(tmp_path: Path) -> None:
    """Default init uses project-local storage under .ledger/archledger/data."""
    result = CliRunner().invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "init",
            "--project-name",
            "demo",
        ],
    )

    assert result.exit_code == 0, result.output
    context = load_project_context(tmp_path)
    expected = tmp_path / ".ledger" / "archledger" / "data"
    assert context.data_root == expected
    assert context.data_storage == "project"
    assert context.data_source == "manifest"

    manifest = tomllib.loads((tmp_path / ".ledger" / "ledger.toml").read_text())
    mount = manifest["ledgers"]["archledger"]["mounts"]["data"]
    assert mount == {
        "storage": "project",
    }
    assert (context.data_root / ".ledger-project.toml").exists()
    assert not (tmp_path / ".ledger" / "ledger.local.toml").exists()
