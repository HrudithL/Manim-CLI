from pathlib import Path

from manim_cli.manim.core.analyze import analyze_scene_file
from manim_cli.manim.core.validate import validate_repo


def test_analyze_scene_file_extracts_play_calls(tmp_path: Path) -> None:
    scene_file = tmp_path / "a.py"
    scene_file.write_text(
        """
from manim import *

class AnalyzeMe(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
""".strip(),
        encoding="utf-8",
    )

    data = analyze_scene_file(str(scene_file))
    assert data["class_count"] == 1
    assert data["classes"][0]["name"] == "AnalyzeMe"
    assert len(data["classes"][0]["play_calls"]) == 1


def test_validate_repo_checks_manim_layout(tmp_path: Path) -> None:
    (tmp_path / "manim").mkdir()
    example = tmp_path / "example.py"
    example.write_text(
        """
from manim import Scene

class V(Scene):
    pass
""".strip(),
        encoding="utf-8",
    )
    result = validate_repo(str(tmp_path))
    assert result["ok"] is True
    assert result["scene_count"] == 1
