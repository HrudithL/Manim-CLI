from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


def build_render_command(
    scene_file: str,
    scene_name: str,
    quality: str = "l",
    renderer: str = "cairo",
    output_dir: str | None = None,
    extra_flags: tuple[str, ...] = (),
) -> list[str]:
    cmd = [
        "manim",
        f"-q{quality}",
        f"--renderer={renderer}",
    ]
    if output_dir:
        cmd.extend(["--media_dir", output_dir])
    cmd.extend([scene_file, scene_name])
    cmd.extend(extra_flags)
    return cmd


def run_render(
    scene_file: str,
    scene_name: str,
    quality: str = "l",
    renderer: str = "cairo",
    output_dir: str | None = None,
    dry_run: bool = False,
    extra_flags: tuple[str, ...] = (),
) -> dict[str, Any]:
    if shutil.which("manim") is None:
        return {
            "ok": False,
            "error": "manim executable not found on PATH",
            "command": [],
            "returncode": 127,
        }

    cmd = build_render_command(
        scene_file=scene_file,
        scene_name=scene_name,
        quality=quality,
        renderer=renderer,
        output_dir=output_dir,
        extra_flags=extra_flags,
    )
    if dry_run:
        return {"ok": True, "dry_run": True, "command": cmd}

    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
    )
    output_root = Path(output_dir).resolve().as_posix() if output_dir else None
    return {
        "ok": proc.returncode == 0,
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "output_root": output_root,
    }
