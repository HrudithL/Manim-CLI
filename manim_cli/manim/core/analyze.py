from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .rules import GlobalRules, default_rules

# Manim color constants used for palette/style detection
_MANIM_COLOR_NAMES = frozenset(
    [
        "RED", "RED_A", "RED_B", "RED_C", "RED_D", "RED_E",
        "ORANGE", "YELLOW", "YELLOW_A", "YELLOW_B", "YELLOW_C", "YELLOW_D", "YELLOW_E",
        "GREEN", "GREEN_A", "GREEN_B", "GREEN_C", "GREEN_D", "GREEN_E",
        "TEAL", "TEAL_A", "TEAL_B", "TEAL_C", "TEAL_D", "TEAL_E",
        "BLUE", "BLUE_A", "BLUE_B", "BLUE_C", "BLUE_D", "BLUE_E",
        "PURPLE", "PURPLE_A", "PURPLE_B", "PURPLE_C", "PURPLE_D", "PURPLE_E",
        "MAROON", "MAROON_A", "MAROON_B", "MAROON_C", "MAROON_D", "MAROON_E",
        "GOLD", "GOLD_A", "GOLD_B", "GOLD_C", "GOLD_D", "GOLD_E",
        "WHITE", "BLACK", "GREY", "GRAY", "GREY_A", "GREY_B", "GREY_C",
        "GREY_BROWN", "DARK_BROWN", "DARK_BLUE",
        "PINK", "LIGHT_PINK", "LIGHT_BROWN",
    ]
)


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return "unknown"


def _extract_policy_facts(tree: ast.AST, scene_file: str) -> dict[str, Any]:
    """Extract policy-relevant AST facts for LLM/diagnostic consumers."""
    color_refs: list[dict[str, Any]] = []
    hex_refs: list[dict[str, Any]] = []
    run_time_refs: list[dict[str, Any]] = []
    add_calls: list[dict[str, Any]] = []
    positioned_calls: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        # Detect Manim color constant references
        if isinstance(node, ast.Name) and node.id in _MANIM_COLOR_NAMES:
            color_refs.append({"name": node.id, "lineno": node.lineno})

        # Detect hex-string color literals (#RRGGBB style)
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.s, str)
            and len(node.s) in (7, 9)
            and node.s.startswith("#")
        ):
            hex_refs.append({"value": node.s, "lineno": node.lineno})

        # Detect explicit run_time keyword args
        if (
            isinstance(node, ast.keyword)
            and node.arg == "run_time"
            and isinstance(node.value, ast.Constant)
        ):
            run_time_refs.append(
                {"value": node.value.value, "lineno": getattr(node.value, "lineno", None)}
            )

        # Detect self.add() calls (overlap risk heuristic)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add"
        ):
            add_calls.append({"lineno": node.lineno})

        # Detect .move_to() / .shift() / .next_to() (positioning mitigators)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("move_to", "shift", "next_to", "to_edge", "to_corner")
        ):
            positioned_calls.append({"method": node.func.attr, "lineno": node.lineno})

    # Sort for determinism
    color_refs.sort(key=lambda x: (x["name"], x["lineno"]))
    hex_refs.sort(key=lambda x: (x["value"], x["lineno"]))
    run_time_refs.sort(key=lambda x: x["lineno"] or 0)
    add_calls.sort(key=lambda x: x["lineno"])
    positioned_calls.sort(key=lambda x: x["lineno"])

    unpositioned_add_risk = max(0, len(add_calls) - len(positioned_calls))

    return {
        "color_constants": color_refs,
        "hex_color_literals": hex_refs,
        "run_time_overrides": run_time_refs,
        "add_calls": add_calls,
        "positioning_calls": positioned_calls,
        "overlap_risk_score": unpositioned_add_risk,
    }


def analyze_scene_file(
    scene_file: str,
    rules: GlobalRules | None = None,
    include_policy_facts: bool = True,
) -> dict[str, Any]:
    if rules is None:
        rules = default_rules()

    path = Path(scene_file)
    if not path.exists():
        raise FileNotFoundError(f"scene file does not exist: {scene_file}")

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    classes: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        class_info: dict[str, Any] = {
            "name": node.name,
            "lineno": node.lineno,
            "play_calls": [],
            "mobject_calls": [],
        }
        for item in node.body:
            if not isinstance(item, ast.FunctionDef) or item.name != "construct":
                continue
            for stmt in ast.walk(item):
                if isinstance(stmt, ast.Call):
                    name = _call_name(stmt)
                    if name == "play":
                        class_info["play_calls"].append({"lineno": stmt.lineno})
                    elif name and name[0].isupper():
                        class_info["mobject_calls"].append(
                            {"name": name, "lineno": stmt.lineno}
                        )
        classes.append(class_info)

    # Sort classes for stable output
    classes.sort(key=lambda c: c["lineno"])

    result: dict[str, Any] = {
        "file": str(path),
        "classes": classes,
        "class_count": len(classes),
    }

    if include_policy_facts:
        result["policy_facts"] = _extract_policy_facts(tree, scene_file)

    return result
