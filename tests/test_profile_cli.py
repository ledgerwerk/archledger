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
    profile_sections = tmp_path / ".archledger" / "profiles" / "arc42" / "sections"
    legacy_sections = tmp_path / ".archledger" / "sections"
    legacy_sections.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(profile_sections), str(legacy_sections))
    config_path = tmp_path / "archledger.toml"
    config_text = config_path.read_text(encoding="utf-8")
    config_text = config_text.replace("config_version = 8", "config_version = 7")
    config_text = config_text.split("[profiles]", 1)[0].rstrip() + "\n"
    config_path.write_text(config_text, encoding="utf-8")

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
    assert (tmp_path / ".archledger" / "profiles" / "arc42" / "sections").is_dir()
    assert "config_version = 8" in config_path.read_text(encoding="utf-8")


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout


def test_profile_enable_bdd_explains_bdd_is_not_a_profile(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "profile", "enable", "bdd"],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert "BDD is not a standalone profile" in payload["error"]["message"]
    assert "profile enable sdd" in payload["error"]["message"]


def test_profile_disable_bdd_explains_bdd_is_not_a_profile(tmp_path: Path) -> None:
    _init(tmp_path)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "profile", "disable", "bdd"],
    )
    assert result.exit_code != 0
    payload = json.loads(result.stdout)
    assert "BDD is not a standalone profile" in payload["error"]["message"]


def test_profile_enable_sdd_preserves_existing_sdd_policy(tmp_path: Path) -> None:
    _init(tmp_path)
    config = tmp_path / "archledger.toml"
    text = config.read_text(encoding="utf-8")
    # First enable sdd so the [profiles.sdd] table exists
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "profile", "enable", "sdd"],
    )
    assert result.exit_code == 0, result.stdout
    # Now modify a BDD-related flag
    text = config.read_text(encoding="utf-8")
    text = text.replace(
        "require_bdd_automation_for_accepted_records = false",
        "require_bdd_automation_for_accepted_records = true",
    )
    config.write_text(text, encoding="utf-8")
    # Re-enable sdd (same state, but should not drop the custom flag)
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "profile", "enable", "sdd"],
    )
    assert result.exit_code == 0, result.stdout
    assert "require_bdd_automation_for_accepted_records = true" in config.read_text(
        encoding="utf-8"
    )
