"""Generate optional integration scaffolds."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archledger.errors import ArchledgerError
from archledger.storage.common import write_text_atomic


@dataclass(frozen=True, slots=True)
class InstallResult:
    target: str
    path: Path
    overwritten: bool


_SCAFFOLDS = {
    "agent-instructions": (
        Path("AGENTS.md"),
        """# Archledger

Use `archledger context`, `archledger trace`, and `archledger sdd check`
before changing architecture-sensitive code. Keep requirement source and test
references current.
""",
    ),
    "github-actions": (
        Path(".github/workflows/archledger.yml"),
        """name: archledger
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install .
      - run: archledger check --strict
      - run: archledger sdd check --strict
""",
    ),
    "pr-template": (
        Path(".github/pull_request_template.md"),
        """## Architecture impact

- [ ] Ran `archledger source changed --fail-on-unlinked`
- [ ] Ran `archledger sdd check --strict`
- [ ] Updated affected records, source refs, and test refs
""",
    ),
    "taskledger-profile": (
        Path(".taskledger/profiles/archledger.toml"),
        """name = "archledger"

[validation]
commands = ["archledger check --strict", "archledger sdd check --strict"]
""",
    ),
}


def install_scaffold(
    workspace_root: Path,
    target: str,
    *,
    force: bool = False,
) -> InstallResult:
    scaffold = _SCAFFOLDS.get(target)
    if scaffold is None:
        raise ArchledgerError(
            "install target must be one of: " + ", ".join(sorted(_SCAFFOLDS))
        )
    relative_path, content = scaffold
    output_path = workspace_root / relative_path
    existed = output_path.exists()
    if existed and not force:
        raise ArchledgerError(
            f"Refusing to overwrite existing file: {relative_path}. Use --force."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(output_path, content)
    return InstallResult(target=target, path=output_path, overwritten=existed)


__all__ = ["InstallResult", "install_scaffold"]
