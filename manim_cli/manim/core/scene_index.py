from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SceneInfo:
    name: str
    file_path: str
    lineno: int


def _is_scene_subclass(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "Scene":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "Scene":
            return True
    return False


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
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and _is_scene_subclass(node):
                results.append(
                    SceneInfo(
                        name=node.name,
                        file_path=str(py_file),
                        lineno=node.lineno,
                    )
                )
    return sorted(results, key=lambda s: (s.file_path, s.lineno, s.name))
