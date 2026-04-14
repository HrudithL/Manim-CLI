from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return "unknown"


def analyze_scene_file(scene_file: str) -> dict[str, Any]:
    path = Path(scene_file)
    if not path.exists():
        raise FileNotFoundError(f"scene file does not exist: {scene_file}")

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    classes: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        class_info: dict[str, Any] = {
            "name": node.name,
            "lineno": node.lineno,
            "play_calls": [],
            "mobject_calls": [],
        }
        for item in node.body:
            if not isinstance(item, ast.FunctionDef) or item.name != "construct":
                continue
            for stmt in ast.walk(item):
                if isinstance(stmt, ast.Call):
                    name = _call_name(stmt)
                    if name == "play":
                        class_info["play_calls"].append({"lineno": stmt.lineno})
                    elif name and name[0].isupper():
                        class_info["mobject_calls"].append(
                            {"name": name, "lineno": stmt.lineno}
                        )
        classes.append(class_info)

    return {
        "file": str(path),
        "classes": classes,
        "class_count": len(classes),
    }
