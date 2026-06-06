from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def test_context_changed_uses_source_baseline_without_crashing(tmp_path: Path) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    snapshot = runner.invoke(
        app,
        ["--root", str(tmp_path), "source", "snapshot"],
    )
    assert snapshot.exit_code == 0, snapshot.stdout
    source.write_text("VALUE = 2\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "context", "--changed"],
    )

    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["result"]["schema"] == "archledger.context.v1"


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout
