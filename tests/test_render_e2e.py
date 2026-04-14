import json
import subprocess
import sys
from pathlib import Path

from manim_cli.manim.utils.output import ENVELOPE_SCHEMA_VERSION


def test_render_dry_run_json_output(tmp_path: Path) -> None:
    scene_file = tmp_path / "scene.py"
    scene_file.write_text(
        "from manim import *\nclass DryRunScene(Scene):\n    def construct(self):\n        self.play(Write(Text('x')))\n",
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
    assert "-ql" in data["render_command"]
    # Envelope contract
    assert data["schema_version"] == ENVELOPE_SCHEMA_VERSION
    assert data["command"] == "render run"
    assert "timestamp" in data
    assert "diagnostics" in data
    assert "policy" in data
