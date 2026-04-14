import json
import subprocess
import sys
from pathlib import Path

from manim_cli.manim._meta import MANIM_CE_VERIFIED_VERSION


def test_cli_version_via_subprocess() -> None:
    cmd = [sys.executable, "-m", "manim_cli.manim.cli", "--version"]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert "Manim CE last verified:" in proc.stdout
    assert MANIM_CE_VERIFIED_VERSION in proc.stdout


def test_cli_json_scene_list_via_subprocess(tmp_path: Path) -> None:
    scene_file = tmp_path / "demo_scene.py"
    scene_file.write_text(
        """
from manim import Scene

class ExampleScene(Scene):
    pass
""".strip(),
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "manim_cli.manim.cli",
        "--json",
        "scene",
        "list",
        "--repo-path",
        str(tmp_path),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["count"] == 1
    assert data["scenes"][0]["name"] == "ExampleScene"
