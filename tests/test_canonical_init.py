from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_init_creates_canonical_repository_layout(tmp_path: Path) -> None:
    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "init"])

    assert result.exit_code == 0
    assert (tmp_path / ".ledger/ledger.toml").is_file()
    assert (tmp_path / ".ledger/archledger/config.toml").is_file()
    assert (tmp_path / ".ledger/archledger/data/storage.yaml").is_file()
    assert not (tmp_path / "archledger.toml").exists()
    assert not (tmp_path / ".archledger.toml").exists()
    config = (tmp_path / ".ledger/archledger/config.toml").read_text()
    assert "config_version = 12" in config
    assert "archledger_dir" not in config
    assert "project_uuid" not in config
    assert "project_name" not in config


def test_init_preserves_unrelated_manifest_and_local_config(tmp_path: Path) -> None:
    (tmp_path / ".ledger").mkdir()
    manifest = """schema_version = 3

[project]
uuid = "12345678-1234-1234-1234-123456789abc"
name = "demo"

# Keep this task registration.
[ledgers.taskledger.mounts.data]
storage = "project"

[ledgers.taskledger.mounts.indexes]
storage = "cache"
"""
    (tmp_path / ".ledger/ledger.toml").write_text(manifest)
    local = (
        "schema_version = 3\n"
        "\n"
        "[ledgers.taskledger.mounts.data]\n"
        'storage = "user-data"\n'
    )
    (tmp_path / ".ledger/ledger.local.toml").write_text(local)

    result = runner.invoke(app, ["--root", str(tmp_path), "init"])

    assert result.exit_code == 0
    mutated = (tmp_path / ".ledger/ledger.toml").read_text()
    assert "# Keep this task registration." in mutated
    assert "[ledgers.taskledger.mounts.data]" in mutated
    assert local == (tmp_path / ".ledger/ledger.local.toml").read_text()
    assert "[ledgers.archledger.mounts.data]" in mutated


def test_init_rejects_legacy_layout_and_arbitrary_storage(tmp_path: Path) -> None:
    (tmp_path / ".archledger.toml").write_text("config_version = 1\n")
    legacy = runner.invoke(app, ["--root", str(tmp_path), "init"])
    assert legacy.exit_code == 1
    assert "migrate project" in legacy.output

    clean = tmp_path / "clean"
    clean.mkdir()
    external = runner.invoke(
        app,
        ["--root", str(clean), "init", "--archledger-dir", "/tmp/external"],
    )
    assert external.exit_code == 1
    assert "no longer supported" in external.output
