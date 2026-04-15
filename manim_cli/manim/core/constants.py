"""Shared constants for the Manim harness."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Scene base classes
# ---------------------------------------------------------------------------

# All first-party Manim CE scene base classes that count as "a scene" for
# discovery purposes.  Keep in sync with Manim CE when bumping
# MANIM_CE_VERIFIED_VERSION.  User-defined intermediate bases are resolved
# transitively per file, so this list only needs Manim's own types.
MANIM_SCENE_BASE_NAMES: frozenset[str] = frozenset(
    [
        "Scene",
        "MovingCameraScene",
        "ThreeDScene",
        "ZoomedScene",
        "LinearTransformationScene",
        "VectorScene",
        "ReconfigurableScene",
        "SampleSpaceScene",
        "SpecialThreeDScene",
    ]
)

# Manim CE named color constants used for palette and style checks.
# Keep this list in sync with Manim CE's COLOR_MAP when bumping
# MANIM_CE_VERIFIED_VERSION in _meta.py.
MANIM_COLOR_NAMES: frozenset[str] = frozenset(
    [
        "RED", "RED_A", "RED_B", "RED_C", "RED_D", "RED_E",
        "ORANGE",
        "YELLOW", "YELLOW_A", "YELLOW_B", "YELLOW_C", "YELLOW_D", "YELLOW_E",
        "GREEN", "GREEN_A", "GREEN_B", "GREEN_C", "GREEN_D", "GREEN_E",
        "TEAL", "TEAL_A", "TEAL_B", "TEAL_C", "TEAL_D", "TEAL_E",
        "BLUE", "BLUE_A", "BLUE_B", "BLUE_C", "BLUE_D", "BLUE_E",
        "PURPLE", "PURPLE_A", "PURPLE_B", "PURPLE_C", "PURPLE_D", "PURPLE_E",
        "MAROON", "MAROON_A", "MAROON_B", "MAROON_C", "MAROON_D", "MAROON_E",
        "GOLD", "GOLD_A", "GOLD_B", "GOLD_C", "GOLD_D", "GOLD_E",
        "WHITE", "BLACK",
        "GREY", "GRAY", "GREY_A", "GREY_B", "GREY_C",
        "GREY_BROWN", "DARK_BROWN", "DARK_BLUE",
        "PINK", "LIGHT_PINK", "LIGHT_BROWN",
    ]
)
