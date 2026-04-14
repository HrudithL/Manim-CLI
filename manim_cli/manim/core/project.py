from __future__ import annotations

from pathlib import Path
from typing import Any

from .rules import GlobalRules, default_rules


# Template embeds semantic style constants and rule-derived defaults so
# generated scenes don't rely on ad-hoc magic values.
_SCENE_TEMPLATE = """\
from manim import *

# --- Style constants (rule-compliant) ---
STROKE_WIDTH = {stroke_width}
FONT_SIZE = {font_size}
ANIMATION_RUN_TIME = {animation_run_time}
FILL_OPACITY = {fill_opacity}


class {scene_name}(Scene):
    def construct(self):
        text = Text("Hello Manim", font_size=FONT_SIZE)
        self.play(Write(text), run_time=ANIMATION_RUN_TIME)
        self.wait(0.5)
"""


def _render_template(scene_name: str, rules: GlobalRules) -> str:
    return _SCENE_TEMPLATE.format(
        scene_name=scene_name,
        stroke_width=rules.style.stroke_width,
        font_size=rules.style.font_size,
        animation_run_time=rules.style.animation_run_time,
        fill_opacity=rules.style.fill_opacity,
    )


def init_project(
    target_dir: str,
    scene_name: str = "HelloScene",
    rules: GlobalRules | None = None,
) -> dict[str, Any]:
    if rules is None:
        rules = default_rules()

    root = Path(target_dir)
    root.mkdir(parents=True, exist_ok=True)
    scene_file = root / "scene.py"
    if scene_file.exists():
        return {
            "ok": False,
            "error": f"scene file already exists: {scene_file}",
            "error_code": "VALIDATION_ERROR",
            "path": str(scene_file),
        }
    scene_file.write_text(_render_template(scene_name, rules), encoding="utf-8")
    return {
        "ok": True,
        "path": str(scene_file),
        "scene_name": scene_name,
        "active_rules": {
            "policy": rules.policy,
            "schema_version": rules.schema_version,
        },
    }
