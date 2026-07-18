from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_profile_migrate_moves_legacy_sections_and_updates_config(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    data_root = tmp_path / ".ledger" / "archledger" / "data"
    profile_sections = data_root / "profiles" / "arc42" / "sections"
    legacy_sections = data_root / "sections"
    legacy_sections.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(profile_sections), str(legacy_sections))

    dry_run = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "profile",
            "migrate",
            "arc42",
        ],
    )
    assert dry_run.exit_code == 0, dry_run.stdout
    assert legacy_sections.is_dir()
    assert json.loads(dry_run.stdout)["result"]["changed"] is True

    applied = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "profile",
            "migrate",
            "arc42",
            "--write",
        ],
    )
    assert applied.exit_code == 0, applied.stdout
    assert (data_root / "profiles" / "arc42" / "sections").is_dir()


def test_profile_enable_sdd_reports_removed_message(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "profile", "enable", "sdd"],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert (
        "Profile 'sdd' has been removed from archledger." in payload["error"]["message"]
    )


def test_profile_enable_bdd_reports_unsupported_message(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "profile", "enable", "bdd"],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert (
        "Profile 'bdd' is not supported by archledger." in payload["error"]["message"]
    )


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout
