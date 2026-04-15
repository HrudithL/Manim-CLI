from pathlib import Path

import pytest

from manim_cli.manim.core.fix import apply_fixes, _patch_color, _patch_run_time
from manim_cli.manim.core.rules import ColorRules, GlobalRules, StyleRules


# ---------------------------------------------------------------------------
# Unit-level patchers
# ---------------------------------------------------------------------------

def test_patch_color_replaces_name() -> None:
    assert _patch_color("        c = Circle(color=RED)\n", "RED", "BLUE") == \
        "        c = Circle(color=BLUE)\n"


def test_patch_color_word_boundary_no_partial_replace() -> None:
    # REDDISH should not be touched when replacing RED
    line = "x = REDDISH or RED\n"
    result = _patch_color(line, "RED", "BLUE")
    assert "REDDISH" in result
    assert result.count("BLUE") == 1


def test_patch_run_time_replaces_value() -> None:
    assert _patch_run_time("self.play(Write(t), run_time=10)\n", 3.0) == \
        "self.play(Write(t), run_time=3.0)\n"


def test_patch_run_time_handles_spacing() -> None:
    assert _patch_run_time("self.play(Write(t), run_time = 10)\n", 3.0) == \
        "self.play(Write(t), run_time = 3.0)\n"


def test_patch_run_time_handles_float_value() -> None:
    assert _patch_run_time("self.play(Write(t), run_time=10.5)\n", 3.0) == \
        "self.play(Write(t), run_time=3.0)\n"


# ---------------------------------------------------------------------------
# apply_fixes: missing file
# ---------------------------------------------------------------------------

def test_apply_fixes_missing_file_returns_error() -> None:
    result = apply_fixes("/nonexistent/scene.py")
    assert result["ok"] is False
    assert result["error_code"] == "FILE_NOT_FOUND"


# ---------------------------------------------------------------------------
# apply_fixes: no violations → nothing to do
# ---------------------------------------------------------------------------

def test_apply_fixes_clean_scene_no_changes(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\nclass S(Scene):\n    def construct(self):\n        pass\n",
        encoding="utf-8",
    )
    result = apply_fixes(str(f))
    assert result["ok"] is True
    assert result["fix_count"] == 0
    assert result["unfixed_count"] == 0


# ---------------------------------------------------------------------------
# apply_fixes: color fix
# ---------------------------------------------------------------------------

def test_apply_fixes_replaces_out_of_palette_color(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    original = (
        "from manim import *\n"
        "class S(Scene):\n"
        "    def construct(self):\n"
        "        c = Circle(color=RED)\n"
        "        self.play(Create(c))\n"
    )
    f.write_text(original, encoding="utf-8")
    rules = GlobalRules(color=ColorRules(approved_palette=["BLUE", "GREEN"]))
    result = apply_fixes(str(f), rules=rules)

    assert result["ok"] is True
    assert result["fix_count"] == 1
    assert result["fixes_applied"][0]["rule_id"] == "color.out_of_palette"
    assert "RED" not in f.read_text(encoding="utf-8")
    assert "BLUE" in f.read_text(encoding="utf-8")


def test_apply_fixes_multiple_colors_same_line(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\n"
        "class S(Scene):\n"
        "    def construct(self):\n"
        "        c = Circle(color=RED, fill_color=GREEN)\n",
        encoding="utf-8",
    )
    # GREEN is in palette, RED is not
    rules = GlobalRules(color=ColorRules(approved_palette=["GREEN"]))
    result = apply_fixes(str(f), rules=rules)

    assert result["fix_count"] == 1
    content = f.read_text(encoding="utf-8")
    assert "RED" not in content


def test_apply_fixes_color_dry_run_does_not_write(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    original = (
        "from manim import *\n"
        "class S(Scene):\n"
        "    def construct(self):\n"
        "        c = Circle(color=RED)\n"
    )
    f.write_text(original, encoding="utf-8")
    rules = GlobalRules(color=ColorRules(approved_palette=["BLUE"]))
    result = apply_fixes(str(f), rules=rules, dry_run=True)

    assert result["dry_run"] is True
    assert result["fix_count"] == 1
    # File should be unchanged
    assert f.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# apply_fixes: run_time fix
# ---------------------------------------------------------------------------

def test_apply_fixes_caps_run_time(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\n"
        "class S(Scene):\n"
        "    def construct(self):\n"
        "        self.play(Write(Text('x')), run_time=10)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(style=StyleRules(animation_run_time=1.0))
    result = apply_fixes(str(f), rules=rules)

    assert result["fix_count"] == 1
    assert result["fixes_applied"][0]["rule_id"] == "style.animation_run_time"
    content = f.read_text(encoding="utf-8")
    assert "run_time=3.0" in content


# ---------------------------------------------------------------------------
# apply_fixes: layout diagnostics are not auto-fixed
# ---------------------------------------------------------------------------

def test_apply_fixes_layout_violations_left_as_unfixed(tmp_path: Path) -> None:
    f = tmp_path / "scene.py"
    f.write_text(
        "from manim import *\n"
        "class S(Scene):\n"
        "    def construct(self):\n"
        "        t = Text('Hello')\n"
        "        self.add(t)\n",
        encoding="utf-8",
    )
    rules = GlobalRules(policy="strict")
    result = apply_fixes(str(f), rules=rules)

    assert result["ok"] is True
    assert result["fix_count"] == 0
    assert result["unfixed_count"] > 0
    rule_ids = {d["rule_id"] for d in result["unfixed_diagnostics"]}
    assert any(rid.startswith("layout.") for rid in rule_ids)
