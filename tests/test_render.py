from pathlib import Path

import pytest

from manim_cli.manim.core.render import _run_policy_checks, build_render_command, run_render
from manim_cli.manim.core.rules import GlobalRules, StyleRules, ColorRules, LayoutRules


def test_build_render_command_contains_expected_parts() -> None:
    cmd = build_render_command(
        scene_file="scene.py",
        scene_name="MyScene",
        quality="l",
        renderer="cairo",
        output_dir="media",
    )
    assert cmd[0] == "manim"
    assert "-ql" in cmd
    assert "--renderer=cairo" in cmd
    assert "--media_dir" in cmd
    assert "scene.py" in cmd
    assert "MyScene" in cmd


def test_build_render_command_no_output_dir() -> None:
    cmd = build_render_command(scene_file="s.py", scene_name="S")
    assert "--media_dir" not in cmd


# ---------------------------------------------------------------------------
# Pre-render policy checks
# ---------------------------------------------------------------------------

def test_policy_checks_empty_file_no_diagnostics(tmp_path: Path) -> None:
    f = tmp_path / "empty.py"
    f.write_text("from manim import *\nclass S(Scene):\n    def construct(self):\n        pass\n", encoding="utf-8")
    rules = GlobalRules()
    diags = _run_policy_checks(str(f), rules)
    assert diags == []


def test_policy_checks_out_of_palette_color(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        c = Circle(color=RED)\n        self.add(c)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(
        color=ColorRules(approved_palette=["BLUE"]),
    )
    diags = _run_policy_checks(str(f), rules)
    assert any(d["rule_id"] == "color.out_of_palette" for d in diags)
    for d in diags:
        assert "rule_id" in d
        assert "severity" in d
        assert "message" in d
        assert "location" in d


def test_policy_checks_no_palette_means_no_color_diag(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        c = Circle(color=RED)\n",
        encoding="utf-8",
    )
    rules = GlobalRules()  # empty approved_palette
    diags = _run_policy_checks(str(f), rules)
    assert not any(d["rule_id"] == "color.out_of_palette" for d in diags)


def test_policy_checks_run_time_exceeds_threshold(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        self.play(Write(Text('x')), run_time=10)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(style=StyleRules(animation_run_time=1.0))
    diags = _run_policy_checks(str(f), rules)
    assert any(d["rule_id"] == "style.animation_run_time" for d in diags)


def test_policy_checks_diagnostics_are_sorted(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n"
        "        c1 = Circle(color=RED)\n        c2 = Square(color=GREEN)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(color=ColorRules(approved_palette=["BLUE"]))
    diags = _run_policy_checks(str(f), rules)
    rule_ids = [d["rule_id"] for d in diags]
    assert rule_ids == sorted(rule_ids)


# ---------------------------------------------------------------------------
# run_render gate behavior
# ---------------------------------------------------------------------------

def test_run_render_strict_policy_blocks_on_warnings(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        c = Circle(color=RED)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(
        color=ColorRules(approved_palette=["BLUE"]),
        policy="strict",
    )
    result = run_render(
        scene_file=str(f),
        scene_name="S",
        dry_run=True,
        rules=rules,
    )
    assert result["ok"] is False
    assert result["error_code"] == "POLICY_VIOLATION"
    assert len(result["diagnostics"]) > 0


def test_run_render_warn_policy_passes_with_warnings(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        c = Circle(color=RED)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(
        color=ColorRules(approved_palette=["BLUE"]),
        policy="warn",
    )
    result = run_render(
        scene_file=str(f),
        scene_name="S",
        dry_run=True,
        rules=rules,
    )
    # warn mode should still proceed (ok=True for dry-run)
    assert result["ok"] is True
    assert len(result["diagnostics"]) > 0


def test_run_render_fix_ready_policy_passes_with_warnings(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        c = Circle(color=RED)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(
        color=ColorRules(approved_palette=["BLUE"]),
        policy="fix-ready",
    )
    result = run_render(
        scene_file=str(f),
        scene_name="S",
        dry_run=True,
        rules=rules,
    )
    assert result["ok"] is True
    assert "diagnostics" in result
