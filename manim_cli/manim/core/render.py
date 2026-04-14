from __future__ import annotations

import ast
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .rules import GlobalRules, default_rules

# ---------------------------------------------------------------------------
# Known Manim color constant names that are not in the approved palette
# (evaluated by heuristic – only flagged when a non-empty palette is defined)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Diagnostic helpers
# ---------------------------------------------------------------------------

def _make_diagnostic(
    rule_id: str,
    severity: str,
    message: str,
    scene_file: str | None = None,
    lineno: int | None = None,
    fix_hint: str | None = None,
) -> dict[str, Any]:
    d: dict[str, Any] = {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
    }
    if scene_file is not None or lineno is not None:
        loc: dict[str, Any] = {}
        if scene_file:
            loc["file"] = scene_file
        if lineno is not None:
            loc["lineno"] = lineno
        d["location"] = loc
    if fix_hint is not None:
        d["fix_hint"] = fix_hint
    return d


def _run_policy_checks(
    scene_file: str,
    rules: GlobalRules,
) -> list[dict[str, Any]]:
    """Produce a stable, sorted list of policy diagnostics for *scene_file*."""
    diagnostics: list[dict[str, Any]] = []
    path = Path(scene_file)
    if not path.exists():
        return diagnostics

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return diagnostics

    approved = {p.upper() for p in rules.color.approved_palette}
    check_palette = bool(approved)

    for node in ast.walk(tree):
        # Detect use of out-of-palette Manim color names when palette defined
        if check_palette and isinstance(node, ast.Name):
            if node.id in _MANIM_COLOR_NAMES and node.id.upper() not in approved:
                diagnostics.append(
                    _make_diagnostic(
                        rule_id="color.out_of_palette",
                        severity="warning",
                        message=(
                            f"color constant '{node.id}' is not in the approved palette"
                        ),
                        scene_file=scene_file,
                        lineno=node.lineno,
                        fix_hint=f"Replace with one of: {sorted(approved)}",
                    )
                )

        # Detect animation run_time exceeding style default (> 3× rule default)
        if (
            isinstance(node, ast.keyword)
            and node.arg == "run_time"
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, (int, float))
        ):
            rt = float(node.value.value)
            threshold = rules.style.animation_run_time * 3
            if rt > threshold:
                diagnostics.append(
                    _make_diagnostic(
                        rule_id="style.animation_run_time",
                        severity="warning",
                        message=(
                            f"run_time={rt} exceeds 3× style default "
                            f"({rules.style.animation_run_time})"
                        ),
                        scene_file=scene_file,
                        lineno=getattr(node.value, "lineno", None),
                        fix_hint=(
                            f"Consider run_time <= {threshold}"
                        ),
                    )
                )

    # Sort for determinism: (rule_id, lineno)
    diagnostics.sort(key=lambda d: (d["rule_id"], d.get("location", {}).get("lineno", 0)))
    return diagnostics


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
    rules: GlobalRules | None = None,
) -> dict[str, Any]:
    if rules is None:
        rules = default_rules()

    if shutil.which("manim") is None:
        return {
            "ok": False,
            "error": "manim executable not found on PATH",
            "error_code": "MANIM_NOT_FOUND",
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

    # Pre-render policy gate
    diagnostics = _run_policy_checks(scene_file, rules)
    errors = [d for d in diagnostics if d["severity"] == "error"]
    warnings = [d for d in diagnostics if d["severity"] == "warning"]

    policy = rules.policy
    gate_blocked = False
    if policy == "strict" and (errors or warnings):
        gate_blocked = True
    elif policy in ("warn", "fix-ready") and errors:
        gate_blocked = True

    if dry_run:
        result: dict[str, Any] = {
            "ok": not gate_blocked,
            "dry_run": True,
            "command": cmd,
            "policy": policy,
            "diagnostics": diagnostics,
        }
        if gate_blocked:
            result["error"] = "pre-render policy gate blocked execution"
            result["error_code"] = "POLICY_VIOLATION"
        return result

    if gate_blocked:
        return {
            "ok": False,
            "error": "pre-render policy gate blocked execution",
            "error_code": "POLICY_VIOLATION",
            "command": cmd,
            "policy": policy,
            "diagnostics": diagnostics,
        }

    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
    )
    output_root = Path(output_dir).resolve().as_posix() if output_dir else None
    result = {
        "ok": proc.returncode == 0,
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "output_root": output_root,
        "policy": policy,
        "diagnostics": diagnostics,
    }
    if not result["ok"]:
        result["error_code"] = "RENDER_FAILED"
    return result
