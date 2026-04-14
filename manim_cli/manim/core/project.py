from __future__ import annotations

from pathlib import Path
from typing import Any


SCENE_TEMPLATE = """from manim import *


class {scene_name}(Scene):
    def construct(self):
        text = Text("Hello Manim")
        self.play(Write(text))
        self.wait(0.5)
"""


def init_project(target_dir: str, scene_name: str = "HelloScene") -> dict[str, Any]:
    root = Path(target_dir)
    root.mkdir(parents=True, exist_ok=True)
    scene_file = root / "scene.py"
    if scene_file.exists():
        return {
            "ok": False,
            "error": f"scene file already exists: {scene_file}",
            "path": str(scene_file),
        }
    scene_file.write_text(SCENE_TEMPLATE.format(scene_name=scene_name), encoding="utf-8")
    return {"ok": True, "path": str(scene_file), "scene_name": scene_name}
