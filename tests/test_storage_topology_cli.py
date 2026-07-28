"""Storage registration and topology command contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app

runner = CliRunner()


def _json(result) -> dict:
    return json.loads(result.stdout)


def _init(root: Path) -> None:
    result = runner.invoke(app, ["--root", str(root), "init"])
    assert result.exit_code == 0, result.output


def test_unregistered_residual_state_is_not_valid(tmp_path: Path) -> None:
    _init(tmp_path)
    manifest = tmp_path / ".ledger" / "ledger.toml"
    text = manifest.read_text(encoding="utf-8")
    start = text.index("[ledgers.archledger")
    end = text.find("[ledgers.", start + 1)
    manifest.write_text(
        text[:start] + (text[end:] if end >= 0 else ""), encoding="utf-8"
    )

    where = runner.invoke(app, ["--root", str(tmp_path), "--json", "storage", "where"])
    validate = runner.invoke(
        app, ["--root", str(tmp_path), "--json", "storage", "validate"]
    )
    assert where.exit_code == 0
    assert _json(where)["result"]["state"] == "unregistered-with-residual-state"
    assert validate.exit_code == 0
    assert _json(validate)["result"]["valid"] is False
    assert _json(validate)["result"]["registered"] is False


def test_storage_set_and_clear_override_do_not_move_data(tmp_path: Path) -> None:
    _init(tmp_path)
    data_root = tmp_path / ".ledger" / "archledger" / "data"
    before_files = sorted(path.relative_to(data_root) for path in data_root.rglob("*"))
    external_root = tmp_path / "external"

    changed = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "storage",
            "set",
            "data",
            "--storage",
            "external",
            "--storage-root",
            str(external_root),
            "--scope",
            "local",
            "--reason",
            "topology test",
        ],
    )
    assert changed.exit_code == 0, changed.output
    changed_payload = _json(changed)["result"]
    assert changed_payload["data_moved"] is False
    assert changed_payload["topology_changed"] is True
    assert (
        sorted(path.relative_to(data_root) for path in data_root.rglob("*"))
        == before_files
    )

    cleared = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "storage",
            "clear-override",
            "data",
            "--reason",
            "restore project topology",
        ],
    )
    assert cleared.exit_code == 0, cleared.output
    assert _json(cleared)["result"]["new_data_root"] == str(data_root)
