"""Tests for the enriched validate_repo checks (requirements, pin, syntax errors)."""

from pathlib import Path

from manim_cli.manim.core.rules import GlobalRules
from manim_cli.manim.core.validate import validate_repo


def _make_valid_repo(root: Path) -> None:
    """Minimal valid repo: manim/ dir + one Scene subclass."""
    (root / "manim").mkdir()
    (root / "scene.py").write_text(
        "from manim import Scene\nclass V(Scene): pass\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Return-shape contract
# ---------------------------------------------------------------------------

def test_validate_repo_has_warnings_key(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    result = validate_repo(str(tmp_path))
    assert "warnings" in result


def test_validate_repo_has_checks_key(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    result = validate_repo(str(tmp_path))
    assert "checks" in result
    for key in ("manim_dir", "requirements_file", "manim_pinned", "syntax_errors"):
        assert key in result["checks"], f"missing check key: {key}"


# ---------------------------------------------------------------------------
# Requirements file check
# ---------------------------------------------------------------------------

def test_validate_repo_warns_missing_requirements(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    result = validate_repo(str(tmp_path))
    assert result["ok"] is True  # warnings don't affect ok
    assert result["checks"]["requirements_file"]["ok"] is False
    assert any("requirements" in w for w in result["warnings"])


def test_validate_repo_accepts_requirements_txt(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    (tmp_path / "requirements.txt").write_text("manim==0.19.0\n", encoding="utf-8")
    result = validate_repo(str(tmp_path))
    assert result["ok"] is True
    assert result["checks"]["requirements_file"]["ok"] is True
    assert result["checks"]["requirements_file"]["found"] == "requirements.txt"


def test_validate_repo_accepts_pyproject_toml(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry.dependencies]\nmanim = "^0.19.0"\n', encoding="utf-8"
    )
    result = validate_repo(str(tmp_path))
    assert result["checks"]["requirements_file"]["found"] == "pyproject.toml"
    assert result["checks"]["manim_pinned"]["ok"] is True


# ---------------------------------------------------------------------------
# Manim pin check
# ---------------------------------------------------------------------------

def test_validate_repo_detects_manim_pin(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    (tmp_path / "requirements.txt").write_text("manim==0.19.0\n", encoding="utf-8")
    result = validate_repo(str(tmp_path))
    assert result["checks"]["manim_pinned"]["ok"] is True
    assert "manim" in result["checks"]["manim_pinned"]["entry"]


def test_validate_repo_warns_manim_not_pinned(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    (tmp_path / "requirements.txt").write_text("click>=8.1\nnumpy\n", encoding="utf-8")
    result = validate_repo(str(tmp_path))
    assert result["ok"] is True
    assert result["checks"]["manim_pinned"]["ok"] is False
    assert any("manim" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Syntax error check
# ---------------------------------------------------------------------------

def test_validate_repo_clean_syntax_passes(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    result = validate_repo(str(tmp_path))
    assert result["checks"]["syntax_errors"]["ok"] is True
    assert result["checks"]["syntax_errors"]["files_with_errors"] == []


def test_validate_repo_syntax_error_sets_ok_false(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    (tmp_path / "bad.py").write_text("def foo(:\n    pass\n", encoding="utf-8")
    result = validate_repo(str(tmp_path))
    assert result["ok"] is False
    assert result["checks"]["syntax_errors"]["ok"] is False
    assert len(result["checks"]["syntax_errors"]["files_with_errors"]) >= 1
    assert any("bad.py" in e["file"] for e in result["checks"]["syntax_errors"]["files_with_errors"])


def test_validate_repo_syntax_error_in_errors_list(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    (tmp_path / "broken.py").write_text("class (\n", encoding="utf-8")
    result = validate_repo(str(tmp_path))
    assert any("broken.py" in e for e in result["errors"])
