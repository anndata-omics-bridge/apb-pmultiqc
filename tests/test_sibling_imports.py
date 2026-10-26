"""Other anndata_bridge packages, and this package's CLI, import only through an api module."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKAGE = "apb_pmultiqc"
FOLDERS = ("src", "tests", "scripts")
# Application pins use Git sources, so boundary coverage must not depend on path sources.
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
SIBLINGS = frozenset(
    dependency.split(" @ ")[0].replace("-", "_")
    for dependency in PYPROJECT["project"]["dependencies"]
    if " @ git+" in dependency
    and dependency.split(" @ ")[0].startswith(("apb", "protein-fasta", "prozor"))
)


def _sibling_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            modules.extend(
                f"{node.module}.{alias.name}" if node.module in SIBLINGS else node.module
                for alias in node.names
            )
    return [module for module in modules if module.split(".")[0] in SIBLINGS]


def test_siblings_are_imported_only_through_their_api() -> None:
    sources = sorted(path for folder in FOLDERS for path in (ROOT / folder).rglob("*.py"))
    offenders = [
        f"{path.relative_to(ROOT)}: {module}"
        for path in sources
        for module in _sibling_modules(path)
        if module != f"{module.split('.')[0]}.api"
    ]
    assert SIBLINGS
    assert offenders == []


def _package_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            modules.append(node.module)
    return [module for module in modules if module.split(".")[0] == PACKAGE]


def test_the_cli_imports_no_private_library_modules() -> None:
    path = ROOT / "src" / PACKAGE / "cli.py"
    assert _package_modules(path) == []
