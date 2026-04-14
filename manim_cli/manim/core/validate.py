from __future__ import annotations

from pathlib import Path
from typing import Any

from .scene_index import discover_scenes


def validate_repo(repo_path: str) -> dict[str, Any]:
    root = Path(repo_path)
    if not root.exists():
        return {"ok": False, "errors": [f"repo path does not exist: {repo_path}"]}
    if not (root / "manim").exists():
        return {
            "ok": False,
            "errors": ["expected repo-first layout with top-level `manim/` package"],
        }

    scenes = discover_scenes(repo_path)
    errors: list[str] = []
    if not scenes:
        errors.append("no Scene subclasses discovered in repository")
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "scene_count": len(scenes),
    }
