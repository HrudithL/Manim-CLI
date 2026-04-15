import json
import subprocess
import sys
from pathlib import Path

import pytest

from manim_cli.manim.core.install import AGENT_TARGET_DIRS, install_skills


# ---------------------------------------------------------------------------
# install_skills: basic copy
# ---------------------------------------------------------------------------

def test_install_skills_ok_with_target_override(tmp_path: Path) -> None:
    result = install_skills(target_override=str(tmp_path))
    assert result["ok"] is True
    assert result["file_count"] > 0
    assert len(result["installed_files"]) == result["file_count"]


def test_install_skills_files_are_md(tmp_path: Path) -> None:
    result = install_skills(target_override=str(tmp_path))
    for path_str in result["installed_files"]:
        assert path_str.endswith(".md"), f"unexpected non-md file: {path_str}"


def test_install_skills_files_exist_on_disk(tmp_path: Path) -> None:
    result = install_skills(target_override=str(tmp_path))
    for path_str in result["installed_files"]:
        assert Path(path_str).exists(), f"installed file missing: {path_str}"


def test_install_skills_creates_nested_target_dir(tmp_path: Path) -> None:
    target = tmp_path / "deep" / "nested" / "dir"
    assert not target.exists()
    result = install_skills(target_override=str(target))
    assert result["ok"] is True
    assert target.exists()


# ---------------------------------------------------------------------------
# install_skills: agent types
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("agent", ["claude", "copilot", "generic"])
def test_install_skills_all_agent_types(tmp_path: Path, agent: str) -> None:
    target = tmp_path / agent
    result = install_skills(agent=agent, target_override=str(target))
    assert result["ok"] is True
    assert result["agent"] == agent
    assert result["file_count"] > 0


def test_install_skills_default_agent_is_claude(tmp_path: Path) -> None:
    result = install_skills(target_override=str(tmp_path))
    assert result["agent"] == "claude"


def test_install_skills_target_dir_in_result(tmp_path: Path) -> None:
    result = install_skills(target_override=str(tmp_path))
    assert result["target_dir"] == str(tmp_path)


# ---------------------------------------------------------------------------
# install_skills: idempotent
# ---------------------------------------------------------------------------

def test_install_skills_idempotent(tmp_path: Path) -> None:
    """Running install twice should succeed and produce the same file count."""
    r1 = install_skills(target_override=str(tmp_path))
    r2 = install_skills(target_override=str(tmp_path))
    assert r2["ok"] is True
    assert r2["file_count"] == r1["file_count"]


# ---------------------------------------------------------------------------
# CLI: install --skills via subprocess
# ---------------------------------------------------------------------------

def _run_cli(*args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "manim_cli.manim.cli", *args]
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def test_install_command_json_output(tmp_path: Path) -> None:
    proc = _run_cli("--json", "install", "--skills", "--target", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["command"] == "install"
    assert data["file_count"] > 0
    assert "installed_files" in data
    assert "target_dir" in data


def test_install_command_agent_override(tmp_path: Path) -> None:
    proc = _run_cli("--json", "install", "--skills", "--agent", "copilot", "--target", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["agent"] == "copilot"
