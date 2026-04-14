import json
import subprocess
import sys
from pathlib import Path


def test_render_dry_run_json_output(tmp_path: Path) -> None:
    scene_file = tmp_path / "scene.py"
    scene_file.write_text(
        """
from manim import *

class DryRunScene(Scene):
    def construct(self):
        self.play(Write(Text("x")))
""".strip(),
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "manim_cli.manim.cli",
        "--json",
        "render",
        "run",
        "--scene-file",
        str(scene_file),
        "--scene-name",
        "DryRunScene",
        "--quality",
        "l",
        "--dry-run",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["dry_run"] is True
    assert "-ql" in data["command"]
