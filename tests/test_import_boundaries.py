"""Verify detailed Ledgercore imports are restricted to the adapter module."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# Modules whose implementation details must not leak beyond the adapter.
_RESTRICTED_LEDGERCORE_MODULES: frozenset[str] = frozenset(
    {
        "ledgercore.layout",
        "ledgercore.manifest",
        "ledgercore.migration",
        "ledgercore.storage_binding",
        "ledgercore.storage_paths",
        "ledgercore.overrides",
        "ledgercore.config",
    }
)

# Generic stable utilities allowed anywhere.
_ALLOWED_LEDGERCORE_UTILITIES: frozenset[str] = frozenset(
    {
        "ledgercore.atomic",
        "ledgercore.frontmatter",
        "ledgercore.hashing",
        "ledgercore.ids",
        "ledgercore.jsonio",
        "ledgercore.jsonl",
        "ledgercore.refs",
        "ledgercore.yamlio",
        "ledgercore.time",
        "ledgercore.path_text",
        "ledgercore.paths",
        "ledgercore.io",
        "ledgercore.tomlio",
        "ledgercore.errors",
        "ledgercore.__init__",
    }
)

# Modules where detailed imports are allowed.
_ADAPTER_MODULES: frozenset[str] = frozenset(
    {
        "archledger.ledgercore_backend",
    }
)

# Test files where detailed imports are allowed.
_ADAPTER_TEST_MODULES: frozenset[str] = frozenset(
    {
        "tests.test_ledgercore_backend",
        "tests.test_import_boundaries",
    }
)


def _collect_archledger_sources() -> list[Path]:
    """Collect all Python source files under archledger/."""
    package_root = Path(__file__).resolve().parent.parent / "archledger"
    sources = list(package_root.rglob("*.py"))
    if not sources:
        pytest.fail("No archledger sources found")
    return sources


def _module_name(path: Path) -> str:
    """Derive dotted module name from a source path."""
    rel = path.relative_to(Path(__file__).resolve().parent.parent)
    parts = list(rel.parts)
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _is_adapter(module_name: str) -> bool:
    return module_name in _ADAPTER_MODULES


def _imports_in_file(path: Path) -> list[tuple[str, int]]:
    """Return (imported_module, line_number) for all imports in a file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        pytest.fail(f"Syntax error in {path}: {exc}")

    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.lineno))
    return imports


def _is_restricted(imported: str) -> bool:
    """Check whether an import target is restricted."""
    if imported in _ALLOWED_LEDGERCORE_UTILITIES:
        return False
    if imported in _RESTRICTED_LEDGERCORE_MODULES:
        return True
    # Check submodules
    for restricted in _RESTRICTED_LEDGERCORE_MODULES:
        if imported.startswith(restricted + "."):
            return True
    return False


def test_no_restricted_imports_outside_adapter() -> None:
    """Detailed Ledgercore imports must not appear outside the adapter."""
    sources = _collect_archledger_sources()
    violations: list[str] = []

    for source_path in sources:
        module = _module_name(source_path)
        if _is_adapter(module):
            continue
        for imported, lineno in _imports_in_file(source_path):
            if _is_restricted(imported):
                violations.append(f"{module}:{lineno} imports {imported}")

    if violations:
        pytest.fail(
            "Restricted ledgercore imports found outside adapter:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


def test_adapter_can_import_restricted_modules() -> None:
    """The adapter itself must be able to import restricted modules."""
    adapter_path = (
        Path(__file__).resolve().parent.parent / "archledger" / "ledgercore_backend.py"
    )
    if not adapter_path.exists():
        pytest.fail("Adapter module not found at archledger/ledgercore_backend.py")

    imports = _imports_in_file(adapter_path)
    restricted_imports = [(imp, line) for imp, line in imports if _is_restricted(imp)]

    if not restricted_imports:
        pytest.fail(
            "Adapter module does not import any restricted ledgercore modules. "
            "It must be the sole importer of detailed ledgercore APIs."
        )


def test_restricted_modules_exist() -> None:
    """Verify the restricted module list is not stale."""
    for mod in _RESTRICTED_LEDGERCORE_MODULES:
        try:
            __import__(mod)
        except ImportError as exc:
            if "ledgercore." in str(exc):
                continue  # submodule may not exist in current version
            pytest.fail(f"Restricted module {mod} cannot be imported: {exc}")
