from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .constants import MANIM_SCENE_BASE_NAMES


@dataclass(frozen=True)
class SceneInfo:
    name: str
    file_path: str
    lineno: int


# ---------------------------------------------------------------------------
# Per-file inheritance helpers
# ---------------------------------------------------------------------------

def _collect_class_bases(tree: ast.AST) -> dict[str, set[str]]:
    """Return {class_name: {immediate_base_names}} for every class in *tree*."""
    class_bases: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases: set[str] = set()
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.add(base.id)
                elif isinstance(base, ast.Attribute):
                    # e.g. manim.Scene → "Scene"
                    bases.add(base.attr)
            class_bases[node.name] = bases
    return class_bases


def _is_scene_subclass(class_name: str, class_bases: dict[str, set[str]]) -> bool:
    """Return True if *class_name* transitively inherits from any Manim scene base.

    Resolves intermediate bases defined in the same file so that patterns like::

        class MyBase(MovingCameraScene): ...
        class MyScene(MyBase): ...         # ← discovered

    are correctly identified without importing the module.
    """
    visited: set[str] = set()
    queue: list[str] = list(class_bases.get(class_name, set()))
    while queue:
        name = queue.pop()
        if name in visited:
            continue
        visited.add(name)
        if name in MANIM_SCENE_BASE_NAMES:
            return True
        queue.extend(class_bases.get(name, set()) - visited)
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def discover_scenes(repo_path: str) -> list[SceneInfo]:
    root = Path(repo_path)
    if not root.exists():
        raise FileNotFoundError(f"repo path does not exist: {repo_path}")

    results: list[SceneInfo] = []
    for py_file in root.rglob("*.py"):
        if any(part.startswith(".") for part in py_file.parts):
            continue
        source = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue

        class_bases = _collect_class_bases(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and _is_scene_subclass(node.name, class_bases):
                results.append(
                    SceneInfo(
                        name=node.name,
                        file_path=str(py_file),
                        lineno=node.lineno,
                    )
                )

    return sorted(results, key=lambda s: (s.file_path, s.lineno, s.name))
