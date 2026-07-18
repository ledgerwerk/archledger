from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


def test_repository_storage_dependencies_are_declared() -> None:
    data = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    dependencies = data["project"]["dependencies"]
    assert any(d.startswith("ledgercore") for d in dependencies)
    assert "tomlkit>=0.12" in dependencies
    assert not any(item.startswith("ledgercore<") for item in dependencies)
