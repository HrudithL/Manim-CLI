from pathlib import Path

import pytest

from manim_cli.manim.core.analyze import analyze_scene_file
from manim_cli.manim.core.rules import ColorRules, GlobalRules
from manim_cli.manim.core.validate import validate_repo, validate_scene_style


# ---------------------------------------------------------------------------
# analyze_scene_file
# ---------------------------------------------------------------------------

def test_analyze_scene_file_extracts_play_calls(tmp_path: Path) -> None:
    scene_file = tmp_path / "a.py"
    scene_file.write_text(
        "from manim import *\nclass AnalyzeMe(Scene):\n    def construct(self):\n        circle = Circle()\n        self.play(Create(circle))\n",
        encoding="utf-8",
    )
    data = analyze_scene_file(str(scene_file))
    assert data["class_count"] == 1
    assert data["classes"][0]["name"] == "AnalyzeMe"
    assert len(data["classes"][0]["play_calls"]) == 1


def test_analyze_includes_policy_facts_by_default(tmp_path: Path) -> None:
    scene_file = tmp_path / "b.py"
    scene_file.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        t = Text('hi', color=RED)\n        self.play(Write(t))\n",
        encoding="utf-8",
    )
    data = analyze_scene_file(str(scene_file))
    assert "policy_facts" in data
    pf = data["policy_facts"]
    assert "color_constants" in pf
    assert "hex_color_literals" in pf
    assert "run_time_overrides" in pf
    assert "add_calls" in pf
    assert "positioning_calls" in pf
    assert "overlap_risk_score" in pf
    assert any(c["name"] == "RED" for c in pf["color_constants"])


def test_analyze_no_policy_facts_when_disabled(tmp_path: Path) -> None:
    scene_file = tmp_path / "c.py"
    scene_file.write_text("from manim import *\nclass S(Scene):\n    def construct(self):\n        pass\n", encoding="utf-8")
    data = analyze_scene_file(str(scene_file), include_policy_facts=False)
    assert "policy_facts" not in data


def test_analyze_hex_color_detected(tmp_path: Path) -> None:
    scene_file = tmp_path / "d.py"
    scene_file.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        c = Circle(color='#FF0000')\n",
        encoding="utf-8",
    )
    data = analyze_scene_file(str(scene_file))
    assert any(h["value"] == "#FF0000" for h in data["policy_facts"]["hex_color_literals"])


def test_analyze_classes_sorted_by_lineno(tmp_path: Path) -> None:
    scene_file = tmp_path / "multi.py"
    scene_file.write_text(
        "from manim import *\nclass B(Scene): pass\nclass A(Scene): pass\n",
        encoding="utf-8",
    )
    data = analyze_scene_file(str(scene_file))
    linenos = [c["lineno"] for c in data["classes"]]
    assert linenos == sorted(linenos)


def test_analyze_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        analyze_scene_file("/nonexistent/path/scene.py")


# ---------------------------------------------------------------------------
# validate_repo
# ---------------------------------------------------------------------------

def test_validate_repo_checks_manim_layout(tmp_path: Path) -> None:
    (tmp_path / "manim").mkdir()
    example = tmp_path / "example.py"
    example.write_text(
        "from manim import Scene\nclass V(Scene):\n    pass\n",
        encoding="utf-8",
    )
    result = validate_repo(str(tmp_path))
    assert result["ok"] is True
    assert result["scene_count"] == 1


def test_validate_repo_missing_path() -> None:
    result = validate_repo("/nonexistent/path")
    assert result["ok"] is False
    assert result["error_code"] == "FILE_NOT_FOUND"


def test_validate_repo_missing_manim_dir(tmp_path: Path) -> None:
    result = validate_repo(str(tmp_path))
    assert result["ok"] is False
    assert result["error_code"] == "VALIDATION_ERROR"


def test_validate_repo_includes_effective_rules(tmp_path: Path) -> None:
    (tmp_path / "manim").mkdir()
    (tmp_path / "s.py").write_text("from manim import Scene\nclass V(Scene): pass\n", encoding="utf-8")
    rules = GlobalRules()
    result = validate_repo(str(tmp_path), rules=rules)
    assert result["ok"] is True
    assert "effective_rules" in result
    assert result["effective_rules"]["policy"] == "warn"


# ---------------------------------------------------------------------------
# validate_scene_style
# ---------------------------------------------------------------------------

def test_validate_scene_style_clean_scene(tmp_path: Path) -> None:
    scene_file = tmp_path / "clean.py"
    scene_file.write_text(
        "from manim import *\nclass Clean(Scene):\n    def construct(self):\n        pass\n",
        encoding="utf-8",
    )
    result = validate_scene_style(str(scene_file))
    assert result["ok"] is True
    assert result["error_count"] == 0
    assert result["warning_count"] == 0
    assert "effective_rules" in result


def test_validate_scene_style_strict_flags_warnings(tmp_path: Path) -> None:
    scene_file = tmp_path / "scene.py"
    scene_file.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        c = Circle(color=RED)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(
        color=ColorRules(approved_palette=["BLUE"]),
        policy="strict",
    )
    result = validate_scene_style(str(scene_file), rules=rules)
    assert result["ok"] is False
    assert result["warning_count"] > 0
    diag_ids = {d["rule_id"] for d in result["diagnostics"]}
    assert "color.out_of_palette" in diag_ids


def test_validate_scene_style_warn_ok_with_warnings(tmp_path: Path) -> None:
    scene_file = tmp_path / "scene.py"
    scene_file.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        c = Circle(color=RED)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(
        color=ColorRules(approved_palette=["BLUE"]),
        policy="warn",
    )
    result = validate_scene_style(str(scene_file), rules=rules)
    assert result["ok"] is True
    assert result["warning_count"] > 0


def test_validate_scene_style_missing_file() -> None:
    result = validate_scene_style("/nonexistent/scene.py")
    assert result["ok"] is False
    assert result["error_code"] == "FILE_NOT_FOUND"
