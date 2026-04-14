from pathlib import Path

from manim_cli.manim.core.scene_index import discover_scenes


def test_discover_scenes_finds_scene_subclasses(tmp_path: Path) -> None:
    sample = tmp_path / "sample.py"
    sample.write_text(
        """
from manim import Scene

class DemoScene(Scene):
    pass
""".strip(),
        encoding="utf-8",
    )

    scenes = discover_scenes(str(tmp_path))
    assert len(scenes) == 1
    assert scenes[0].name == "DemoScene"
    assert scenes[0].file_path.endswith("sample.py")
