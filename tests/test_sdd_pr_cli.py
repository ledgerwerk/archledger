from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_sdd_check_pr_compares_against_git_revision(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test User"],
        check=True,
    )
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-qm", "baseline"],
        check=True,
    )
    baseline = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    source.write_text("VALUE = 2\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "sdd",
            "check-pr",
            "--against",
            baseline,
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)["result"]
    assert payload["schema"] == "archledger.sdd-pr.v1"
    assert payload["changes"]["changes"]["modified"][0]["path"] == "src/feature.py"


def _init(path: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(path), "init", "--profile", "sdd"],
    )
    assert result.exit_code == 0, result.stdout
