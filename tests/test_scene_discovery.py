"""Tests for richer scene discovery — transitive inheritance detection."""

from pathlib import Path

import pytest

from manim_cli.manim.core.scene_index import _collect_class_bases, _is_scene_subclass, discover_scenes


# ---------------------------------------------------------------------------
# discover_scenes: known Manim base types
# ---------------------------------------------------------------------------

def test_discovers_direct_scene_subclass(tmp_path: Path) -> None:
    (tmp_path / "s.py").write_text(
        "from manim import *\nclass Foo(Scene): pass\n", encoding="utf-8"
    )
    scenes = discover_scenes(str(tmp_path))
    assert len(scenes) == 1
    assert scenes[0].name == "Foo"


def test_discovers_moving_camera_scene(tmp_path: Path) -> None:
    (tmp_path / "s.py").write_text(
        "from manim import *\nclass Cam(MovingCameraScene): pass\n", encoding="utf-8"
    )
    assert any(s.name == "Cam" for s in discover_scenes(str(tmp_path)))


def test_discovers_threed_scene(tmp_path: Path) -> None:
    (tmp_path / "s.py").write_text(
        "from manim import *\nclass Three(ThreeDScene): pass\n", encoding="utf-8"
    )
    assert any(s.name == "Three" for s in discover_scenes(str(tmp_path)))


def test_discovers_zoomed_scene(tmp_path: Path) -> None:
    (tmp_path / "s.py").write_text(
        "from manim import *\nclass Zoomed(ZoomedScene): pass\n", encoding="utf-8"
    )
    assert any(s.name == "Zoomed" for s in discover_scenes(str(tmp_path)))


# ---------------------------------------------------------------------------
# discover_scenes: transitive inheritance within a file
# ---------------------------------------------------------------------------

def test_discovers_transitive_subclass_within_file(tmp_path: Path) -> None:
    """class MyBase(MovingCameraScene) + class MyScene(MyBase) → both discovered."""
    (tmp_path / "s.py").write_text(
        "from manim import *\n"
        "class MyBase(MovingCameraScene): pass\n"
        "class MyScene(MyBase): pass\n",
        encoding="utf-8",
    )
    names = {s.name for s in discover_scenes(str(tmp_path))}
    assert "MyBase" in names
    assert "MyScene" in names


def test_transitive_chain_three_levels(tmp_path: Path) -> None:
    (tmp_path / "s.py").write_text(
        "from manim import *\n"
        "class A(Scene): pass\n"
        "class B(A): pass\n"
        "class C(B): pass\n",
        encoding="utf-8",
    )
    names = {s.name for s in discover_scenes(str(tmp_path))}
    assert names == {"A", "B", "C"}


def test_non_scene_class_not_discovered(tmp_path: Path) -> None:
    (tmp_path / "s.py").write_text(
        "class Helper: pass\nclass Util(Helper): pass\n", encoding="utf-8"
    )
    assert discover_scenes(str(tmp_path)) == []


def test_circular_inheritance_does_not_hang(tmp_path: Path) -> None:
    # Technically invalid Python but the AST parser still produces nodes.
    (tmp_path / "s.py").write_text(
        "class A(B): pass\nclass B(A): pass\n", encoding="utf-8"
    )
    result = discover_scenes(str(tmp_path))
    assert result == []


# ---------------------------------------------------------------------------
# _collect_class_bases helper
# ---------------------------------------------------------------------------

def test_collect_class_bases_simple() -> None:
    import ast
    tree = ast.parse("class A(B, C): pass\nclass D(A): pass\n")
    bases = _collect_class_bases(tree)
    assert bases["A"] == {"B", "C"}
    assert bases["D"] == {"A"}


def test_collect_class_bases_attribute_base() -> None:
    import ast
    tree = ast.parse("import manim\nclass S(manim.Scene): pass\n")
    bases = _collect_class_bases(tree)
    assert "Scene" in bases["S"]


# ---------------------------------------------------------------------------
# _is_scene_subclass helper
# ---------------------------------------------------------------------------

def test_is_scene_subclass_direct() -> None:
    assert _is_scene_subclass("S", {"S": {"Scene"}}) is True


def test_is_scene_subclass_transitive() -> None:
    class_bases = {"MyBase": {"MovingCameraScene"}, "MyScene": {"MyBase"}}
    assert _is_scene_subclass("MyScene", class_bases) is True


def test_is_scene_subclass_unrelated() -> None:
    assert _is_scene_subclass("Foo", {"Foo": {"Bar"}, "Bar": {"Baz"}}) is False
