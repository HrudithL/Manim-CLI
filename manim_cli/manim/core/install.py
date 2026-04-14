from __future__ import annotations

import importlib.resources
import shutil
from pathlib import Path
from typing import Any


AGENT_TARGET_DIRS = {
    "claude": ".claude/skills/manim-cli",
    "copilot": ".github/skills/manim-cli",
    "generic": "skills/manim-cli",
}

SKILL_PACKAGE = "manim_cli.skills"
SKILL_SUBDIR = "manim-cli"


def _resolve_skill_source() -> Path:
    """Locate the bundled skill files inside the installed package."""
    ref = importlib.resources.files(SKILL_PACKAGE).joinpath(SKILL_SUBDIR)
    if hasattr(ref, "_path"):
        return Path(ref._path)
    return Path(str(ref))


def install_skills(
    agent: str = "claude",
    target_override: str | None = None,
) -> dict[str, Any]:
    """Copy bundled skill markdown files to the agent-specific target directory.

    Returns a result dict compatible with the CLI JSON envelope contract.
    """
    source_dir = _resolve_skill_source()
    if not source_dir.is_dir():
        return {
            "ok": False,
            "error": f"Bundled skill directory not found: {source_dir}",
            "error_code": "FILE_NOT_FOUND",
        }

    md_files = sorted(source_dir.glob("*.md"))
    if not md_files:
        return {
            "ok": False,
            "error": f"No .md skill files found in {source_dir}",
            "error_code": "FILE_NOT_FOUND",
        }

    if target_override:
        target_dir = Path(target_override)
    else:
        target_dir = Path(AGENT_TARGET_DIRS.get(agent, AGENT_TARGET_DIRS["generic"]))

    target_dir.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []
    for src_file in md_files:
        dst = target_dir / src_file.name
        shutil.copy2(src_file, dst)
        installed.append(str(dst))

    return {
        "ok": True,
        "agent": agent,
        "target_dir": str(target_dir),
        "installed_files": installed,
        "file_count": len(installed),
    }
