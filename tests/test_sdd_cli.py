from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)

runner = CliRunner()


def test_sdd_check_reports_missing_source_and_test_refs(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Traceable requirement",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    result = json.loads(created.stdout)["result"]
    record_path = Path(result["path"])
    metadata, _body = read_front_matter_document(record_path)
    metadata["source_refs"] = [{"path": "src/missing.py", "role": "implements"}]
    metadata["test_refs"] = ["tests/test_missing.py::test_it"]
    metadata["acceptance_criteria"] = [{"statement": "It works."}]
    write_front_matter_document(record_path, metadata, "Implemented requirement.\n")

    checked = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "sdd", "check"],
    )

    assert checked.exit_code == 1
    payload = json.loads(checked.stdout)
    codes = {item["code"] for item in payload["error"]["details"]["errors"]}
    assert "SDD-SOURCE-REF-EXISTS" in codes
    assert "SDD-TEST-REF-EXISTS" in codes


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init", "--profile", "sdd"])
    assert result.exit_code == 0, result.stdout
