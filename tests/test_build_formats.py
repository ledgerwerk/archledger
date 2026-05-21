from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from archledger.assembly import assemble_document
from archledger.cli import app
from archledger.repository import ArchitectureRepository
from archledger.storage.paths import resolve_project_paths

runner = CliRunner()


def test_build_format_inferred_from_output_extension(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)
    monkeypatch.setattr("archledger.converters.shutil.which", _fake_which)

    captured: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        captured.append(command)
        output_index = command.index("-o") + 1
        output_path = Path(command[output_index])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("converted", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("archledger.converters.subprocess.run", fake_run)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "build", "--output", "docs/architecture.md"],
    )

    assert result.exit_code == 0
    assert (tmp_path / "docs" / "architecture.md").is_file()
    assert captured[0] == [
        "/usr/bin/asciidoctor",
        "-a",
        "skip-front-matter",
        "-b",
        "docbook5",
        "-o",
        str(tmp_path / "build" / "architecture.docbook.xml"),
        str(tmp_path / "build" / "architecture.adoc"),
    ]
    assert captured[1][:5] == [
        "/usr/bin/pandoc",
        "-f",
        "docbook",
        "-t",
        "gfm",
    ]


def test_build_html_requires_asciidoctor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)
    monkeypatch.setattr("archledger.converters.shutil.which", lambda name: None)

    result = runner.invoke(app, ["--root", str(tmp_path), "build", "--format", "html"])

    assert result.exit_code == 1
    assert "Cannot build html" in result.output
    assert "asciidoctor executable was not found" in result.output


def test_build_pdf_requires_asciidoctor_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)
    monkeypatch.setattr("archledger.converters.shutil.which", lambda name: None)

    result = runner.invoke(app, ["--root", str(tmp_path), "build", "--format", "pdf"])

    assert result.exit_code == 1
    assert "Cannot build pdf" in result.output
    assert "asciidoctor-pdf executable was not found" in result.output


def test_pandoc_backed_format_requires_asciidoctor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)

    def fake_which(name: str) -> str | None:
        if name == "pandoc":
            return "/usr/bin/pandoc"
        return None

    monkeypatch.setattr("archledger.converters.shutil.which", fake_which)

    result = runner.invoke(app, ["--root", str(tmp_path), "build", "--format", "rst"])

    assert result.exit_code == 1
    assert "Cannot build rst" in result.output
    assert "asciidoctor executable was not found" in result.output


def test_build_docx_requires_pandoc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)

    def fake_which(name: str) -> str | None:
        if name == "asciidoctor":
            return "/usr/bin/asciidoctor"
        return None

    monkeypatch.setattr("archledger.converters.shutil.which", fake_which)

    result = runner.invoke(app, ["--root", str(tmp_path), "build", "--format", "docx"])

    assert result.exit_code == 1
    assert "Cannot build docx" in result.output
    assert "pandoc executable was not found" in result.output


@pytest.mark.parametrize(
    ("requested_format", "pandoc_target"),
    [
        ("docx", "docx"),
        ("markdown", "gfm"),
        ("rst", "rst"),
        ("textile", "textile"),
    ],
)
def test_pandoc_command_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    requested_format: str,
    pandoc_target: str,
) -> None:
    init_project(tmp_path)
    monkeypatch.setattr("archledger.converters.shutil.which", _fake_which)

    captured: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        captured.append(command)
        output_index = command.index("-o") + 1
        output_path = Path(command[output_index])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("converted", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("archledger.converters.subprocess.run", fake_run)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "build", "--format", requested_format],
    )

    assert result.exit_code == 0
    assert captured[0][0] == "/usr/bin/asciidoctor"
    assert captured[0][1:6] == ["-a", "skip-front-matter", "-b", "docbook5", "-o"]
    assert captured[1][:5] == ["/usr/bin/pandoc", "-f", "docbook", "-t", pandoc_target]


def test_json_build_reports_multiple_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)
    monkeypatch.setattr("archledger.converters.shutil.which", _fake_which)

    def fake_run(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        output_index = command.index("-o") + 1
        output_path = Path(command[output_index])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("converted", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("archledger.converters.subprocess.run", fake_run)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "--json", "build", "--formats", "html,markdown"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"]["assembled_path"].endswith("architecture.adoc")
    outputs = payload["result"]["outputs"]
    assert [item["format"] for item in outputs] == ["html", "markdown"]
    assert outputs[0]["output_path"].endswith("architecture.html")
    assert outputs[1]["output_path"].endswith("architecture.md")


def test_default_build_includes_enabled_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + "\n[build.outputs.html]\nenabled = true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("archledger.converters.shutil.which", _fake_which)

    def fake_run(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        output_index = command.index("-o") + 1
        output_path = Path(command[output_index])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("converted", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("archledger.converters.subprocess.run", fake_run)

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "build"])

    assert result.exit_code == 0
    outputs = json.loads(result.stdout)["result"]["outputs"]
    assert [item["format"] for item in outputs] == ["asciidoc", "html"]
    assert outputs[0]["output_path"].endswith("architecture.adoc")
    assert outputs[1]["output_path"].endswith("architecture.html")


def test_build_all_honors_disabled_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + "\n[build.outputs.html]\nenabled = false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("archledger.converters.shutil.which", _fake_which)

    def fake_run(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        output_index = command.index("-o") + 1
        output_path = Path(command[output_index])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("converted", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("archledger.converters.subprocess.run", fake_run)

    result = runner.invoke(app, ["--root", str(tmp_path), "--json", "build", "--all"])

    assert result.exit_code == 0
    outputs = json.loads(result.stdout)["result"]["outputs"]
    assert "html" not in [item["format"] for item in outputs]


def test_explicit_format_overrides_disabled_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project(tmp_path)
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + "\n[build.outputs.html]\nenabled = false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("archledger.converters.shutil.which", _fake_which)

    def fake_run(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        output_index = command.index("-o") + 1
        output_path = Path(command[output_index])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("converted", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("archledger.converters.subprocess.run", fake_run)

    result = runner.invoke(app, ["--root", str(tmp_path), "build", "--format", "html"])

    assert result.exit_code == 0
    assert (tmp_path / "build" / "architecture.html").is_file()


def init_project(tmp_path: Path) -> None:
    init_project_with_format(tmp_path)


def init_project_with_format(tmp_path: Path, source_format: str = "asciidoc") -> None:
    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "init", "--source-format", source_format],
    )
    assert result.exit_code == 0


def _fake_which(name: str) -> str | None:
    if name in {"asciidoctor", "asciidoctor-pdf", "pandoc"}:
        return f"/usr/bin/{name}"
    return None


def test_markdown_source_markdown_build_requires_no_tools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project_with_format(tmp_path, "markdown")
    monkeypatch.setattr("archledger.converters.shutil.which", lambda name: None)

    def fail_run(*args: object, **kwargs: object) -> None:
        raise AssertionError("native markdown build should not invoke converters")

    monkeypatch.setattr("archledger.converters.subprocess.run", fail_run)

    result = runner.invoke(
        app, ["--root", str(tmp_path), "build", "--format", "markdown"]
    )

    assert result.exit_code == 0
    assert (tmp_path / "build" / "architecture.md").is_file()


def test_asciidoc_source_asciidoc_build_requires_no_tools(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project_with_format(tmp_path, "asciidoc")
    monkeypatch.setattr("archledger.converters.shutil.which", lambda name: None)

    def fail_run(*args: object, **kwargs: object) -> None:
        raise AssertionError("native asciidoc build should not invoke converters")

    monkeypatch.setattr("archledger.converters.subprocess.run", fail_run)

    result = runner.invoke(
        app, ["--root", str(tmp_path), "build", "--format", "asciidoc"]
    )

    assert result.exit_code == 0
    assert (tmp_path / "build" / "architecture.adoc").is_file()


def test_assemble_document_uses_configured_default_output_for_native_format(
    tmp_path: Path,
) -> None:
    init_project_with_format(tmp_path, "markdown")
    config_path = tmp_path / "archledger.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'default_output = "architecture.md"',
            'default_output = "ARCHITECTURE.md"',
        ),
        encoding="utf-8",
    )

    paths, config, _ = resolve_project_paths(tmp_path)
    repo = ArchitectureRepository(paths, config)

    result = assemble_document(repo, source_format="markdown")

    assert result.output_path == tmp_path / "build" / "ARCHITECTURE.md"
    assert result.output_path.is_file()


@pytest.mark.parametrize(
    ("requested_format", "pandoc_target"),
    [
        ("html", "html5"),
        ("docx", "docx"),
        ("rst", "rst"),
        ("textile", "textile"),
    ],
)
def test_markdown_source_pandoc_backed_formats_use_pandoc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    requested_format: str,
    pandoc_target: str,
) -> None:
    init_project_with_format(tmp_path, "markdown")
    monkeypatch.setattr("archledger.converters.shutil.which", _fake_which)

    captured: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        captured.append(command)
        output_index = command.index("-o") + 1
        output_path = Path(command[output_index])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("converted", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("archledger.converters.subprocess.run", fake_run)

    result = runner.invoke(
        app,
        ["--root", str(tmp_path), "build", "--format", requested_format],
    )

    assert result.exit_code == 0
    assert captured[0][:5] == ["/usr/bin/pandoc", "-f", "gfm", "-t", pandoc_target]


def test_markdown_source_pdf_uses_pandoc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_project_with_format(tmp_path, "markdown")
    monkeypatch.setattr("archledger.converters.shutil.which", _fake_which)

    captured: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        del check, capture_output, text
        captured.append(command)
        output_index = command.index("-o") + 1
        output_path = Path(command[output_index])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("converted", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("archledger.converters.subprocess.run", fake_run)

    result = runner.invoke(app, ["--root", str(tmp_path), "build", "--format", "pdf"])

    assert result.exit_code == 0
    assert captured[0][0:3] == ["/usr/bin/pandoc", "-f", "gfm"]
    assert str(tmp_path / "build" / "architecture.md") in captured[0]
