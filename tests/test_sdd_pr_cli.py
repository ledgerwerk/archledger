from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.frontmatter import (
    read_front_matter_document,
    write_front_matter_document,
)

runner = CliRunner()


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test User"],
        check=True,
    )


def _commit(path: Path, message: str = "baseline") -> str:
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", message], check=True)
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init", "--profile", "sdd"])
    assert result.exit_code == 0, result.stdout


def test_sdd_check_pr_fails_on_unlinked_changed_file(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    baseline = _commit(tmp_path)
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

    assert result.exit_code == 1, result.stdout
    payload = json.loads(result.stdout)["error"]["details"]
    assert payload["schema"] == "archledger.sdd-pr.v1"
    assert payload["changes"]["changes"]["modified"][0]["path"] == "src/feature.py"
    assert "src/feature.py" in payload["changes"]["impact"]["unlinked_changed_files"]


def test_sdd_check_pr_passes_when_changed_file_has_source_ref(
    tmp_path: Path,
) -> None:
    _git_init(tmp_path)
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_value():\n    assert True\n", encoding="utf-8")
    created = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "new",
            "requirement",
            "Feature",
            "--status",
            "accepted",
        ],
    )
    assert created.exit_code == 0, created.stdout
    record_path = Path(json.loads(created.stdout)["result"]["path"])
    metadata, _body = read_front_matter_document(record_path)
    metadata["source_refs"] = [{"path": "src/feature.py", "role": "implements"}]
    metadata["test_refs"] = ["tests/test_feature.py::test_value"]
    metadata["acceptance_criteria"] = [{"statement": "It works."}]
    write_front_matter_document(
        record_path, metadata, "Implemented requirement with a real body.\n"
    )
    baseline = _commit(tmp_path)
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


def test_sdd_check_pr_can_allow_unlinked_when_explicitly_requested(
    tmp_path: Path,
) -> None:
    _git_init(tmp_path)
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    baseline = _commit(tmp_path)
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
            "--allow-unlinked",
        ],
    )

    assert result.exit_code == 0, result.stdout
