from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from archledger.cli import app
from archledger.storage.frontmatter import read_front_matter_document

runner = CliRunner()


def test_nested_mutation_commands_update_record(tmp_path: Path) -> None:
    _init(tmp_path)
    source = tmp_path / "src" / "feature.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "Feature"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    body = tmp_path / "body.md"
    body.write_text("More detail.\n", encoding="utf-8")

    commands = [
        ["record", "set", record_id, "--status", "proposed"],
        ["record", "meta", "set", record_id, "priority", "must"],
        ["record", "body", "append", record_id, "--file", str(body)],
        ["refs", "add", record_id, "--path", "src/feature.py", "--role", "implements"],
        ["ac", "add", record_id, "--statement", "Feature works"],
    ]
    for command in commands:
        result = runner.invoke(app, ["--root", str(tmp_path), *command])
        assert result.exit_code == 0, result.stdout

    text = record_path.read_text(encoding="utf-8")
    assert "status: proposed" in text
    assert "priority: must" in text
    assert "More detail." in text
    assert "role: implements" in text
    assert "Feature works" in text


def _init(path: Path) -> None:
    result = runner.invoke(app, ["--root", str(path), "init"])
    assert result.exit_code == 0, result.stdout


def test_record_body_set_replaces_body_and_validates_record(tmp_path: Path) -> None:
    """P0: record body set replaces (not appends) the body and revalidates."""
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "R"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    body_file = tmp_path / "new_body.md"
    body_file.write_text("# Replaced body\n\nReal content.\n", encoding="utf-8")
    # The template placeholder snippet must be replaced.
    from archledger.checks import PLACEHOLDER_SNIPPETS

    before = record_path.read_text(encoding="utf-8")
    assert any(snip in before for snip in PLACEHOLDER_SNIPPETS)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "body",
            "set",
            record_id,
            "--from-file",
            str(body_file),
        ],
    )
    assert result.exit_code == 0, result.stdout
    after = record_path.read_text(encoding="utf-8")
    assert "# Replaced body" in after
    assert "Real content." in after
    for snip in PLACEHOLDER_SNIPPETS:
        assert snip not in after, f"placeholder {snip!r} still present after set"


def test_record_body_set_text_replaces_body(tmp_path: Path) -> None:
    """record body set --text replaces the body inline."""
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "R"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "body",
            "set",
            record_id,
            "--text",
            "Inline replacement body.",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Inline replacement body." in record_path.read_text(encoding="utf-8")


def test_record_meta_set_rejects_plain_string_for_string_list_field_without_changes(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime", "CLI execution"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    before_bytes = record_path.read_bytes()
    before_metadata, _ = read_front_matter_document(record_path)

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "meta",
            "set",
            record_id,
            "participants",
            "task create",
        ],
    )

    assert result.exit_code == 1
    message = json.loads(result.stdout)["error"]["message"]
    assert (
        "metadata field 'participants' must be a list of strings; got string."
        in message
    )
    assert "--json-value '[\"item\"]'" in message
    assert record_path.read_bytes() == before_bytes
    after_metadata, _ = read_front_matter_document(record_path)
    assert after_metadata["version"] == before_metadata["version"]


def test_record_meta_set_accepts_json_value_for_string_list_field(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "runtime", "CLI execution"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "meta",
            "set",
            record_id,
            "participants",
            "--json-value",
            '["caller", "service"]',
        ],
    )

    assert result.exit_code == 0, result.stdout
    metadata, _ = read_front_matter_document(record_path)
    assert metadata["participants"] == ["caller", "service"]
    assert metadata["version"] == 2


def test_record_meta_set_accepts_option_like_string_with_explicit_string_value(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "Feature"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "meta",
            "set",
            record_id,
            "source",
            "--string-value",
            "--json envelopes are supported",
        ],
    )

    assert result.exit_code == 0, result.stdout
    metadata, _ = read_front_matter_document(record_path)
    assert metadata["source"] == "--json envelopes are supported"


def test_record_apply_noop_does_not_bump_version(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "Feature"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    exported = tmp_path / "record.md"

    export_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "export",
            record_id,
            "--output",
            str(exported),
        ],
    )
    assert export_result.exit_code == 0, export_result.stdout

    apply_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "apply",
            record_id,
            "--from-file",
            str(exported),
        ],
    )

    assert apply_result.exit_code == 0, apply_result.stdout
    assert json.loads(apply_result.stdout)["result"]["changed"] is False
    metadata, _ = read_front_matter_document(record_path)
    assert metadata["version"] == 1


def test_record_apply_rejects_kind_change_and_restores_original(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "Feature"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    original_bytes = record_path.read_bytes()
    exported = tmp_path / "record.md"

    export_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "export",
            record_id,
            "--output",
            str(exported),
        ],
    )
    assert export_result.exit_code == 0, export_result.stdout
    exported.write_text(
        exported.read_text(encoding="utf-8").replace("kind: content", "kind: adr"),
        encoding="utf-8",
    )

    apply_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "apply",
            record_id,
            "--from-file",
            str(exported),
        ],
    )

    assert apply_result.exit_code == 1
    assert "Record kind mismatch" in json.loads(apply_result.stdout)["error"]["message"]
    assert record_path.read_bytes() == original_bytes


def test_record_apply_updates_record_and_bumps_version_once(tmp_path: Path) -> None:
    _init(tmp_path)
    created = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "new", "requirement", "Feature"],
    )
    payload = json.loads(created.stdout)["result"]
    record_id = payload["id"]
    record_path = Path(payload["path"])
    exported = tmp_path / "record.md"

    export_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "export",
            record_id,
            "--output",
            str(exported),
        ],
    )
    assert export_result.exit_code == 0, export_result.stdout
    exported.write_text(
        exported.read_text(encoding="utf-8").replace(
            "Describe this requirement.", "Updated requirement body."
        ),
        encoding="utf-8",
    )

    apply_result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--json",
            "record",
            "apply",
            record_id,
            "--from-file",
            str(exported),
        ],
    )

    assert apply_result.exit_code == 0, apply_result.stdout
    assert json.loads(apply_result.stdout)["result"]["changed"] is True
    metadata, body = read_front_matter_document(record_path)
    assert metadata["version"] == 2
    assert "Updated requirement body." in body
