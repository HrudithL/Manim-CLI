from __future__ import annotations

import ast
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .constants import MANIM_COLOR_NAMES
from .rules import GlobalRules, default_rules


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
            if node.id in MANIM_COLOR_NAMES and node.id.upper() not in approved:
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

    diagnostics.extend(_run_layout_checks(tree=tree, scene_file=scene_file, rules=rules))

    # Sort for determinism: (rule_id, lineno)
    diagnostics.sort(key=lambda d: (d["rule_id"], d.get("location", {}).get("lineno", 0)))
    return diagnostics


def _run_layout_checks(
    tree: ast.AST,
    scene_file: str,
    rules: GlobalRules,
) -> list[dict[str, Any]]:
    """
    Conservative AST-based layout checks.

    These checks intentionally fail early when placement intent is ambiguous.
    They provide deterministic CI enforcement for obvious overlap/clipping risks.
    """
    diagnostics: list[dict[str, Any]] = []

    positioned_vars: set[str] = set()
    constructed_vars: dict[str, str] = {}
    axes_vars: set[str] = set()
    label_vars: set[str] = set()
    graph_like_vars: set[str] = set()

    axis_ctor_names = {"Axes", "NumberPlane", "ThreeDAxes"}
    label_ctor_names = {"Text", "Tex", "MathTex", "DecimalNumber", "Integer"}
    graph_call_attrs = {"plot", "plot_line_graph", "get_graph", "plot_parametric_curve"}
    position_methods = {"move_to", "shift", "next_to", "to_edge", "to_corner", "arrange"}

    def _var_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        return None

    def _const_number(node: ast.AST) -> float | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            ctor_name = None
            if isinstance(node.value.func, ast.Name):
                ctor_name = node.value.func.id
            if ctor_name is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constructed_vars[target.id] = ctor_name
                    if ctor_name in axis_ctor_names:
                        axes_vars.add(target.id)
                    if ctor_name in label_ctor_names:
                        label_vars.add(target.id)

        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr in graph_call_attrs
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    graph_like_vars.add(target.id)

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            method = node.func.attr
            owner_name = _var_name(node.func.value)
            if owner_name and method in position_methods:
                positioned_vars.add(owner_name)

            if owner_name and method == "to_edge":
                margin = rules.layout.frame_margin
                buff_value = None
                for kw in node.keywords:
                    if kw.arg == "buff":
                        buff_value = _const_number(kw.value)
                        break
                if owner_name in axes_vars and buff_value is not None and buff_value < margin:
                    diagnostics.append(
                        _make_diagnostic(
                            rule_id="layout.axis_frame_margin",
                            severity="warning",
                            message=(
                                f"axis '{owner_name}' uses to_edge(buff={buff_value}) below "
                                f"required frame_margin={margin}"
                            ),
                            scene_file=scene_file,
                            lineno=node.lineno,
                            fix_hint=(
                                f"Increase buff to >= {margin} to avoid axis clipping at frame edge"
                            ),
                        )
                    )

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
        ):
            for arg in node.args:
                arg_name = _var_name(arg)
                if not arg_name:
                    continue
                if arg_name not in positioned_vars:
                    diagnostics.append(
                        _make_diagnostic(
                            rule_id="layout.unpositioned_add",
                            severity="warning",
                            message=(
                                f"'{arg_name}' is added without explicit positioning; "
                                "this can cause overlap with existing mobjects"
                            ),
                            scene_file=scene_file,
                            lineno=node.lineno,
                            fix_hint=(
                                f"Call {arg_name}.next_to()/move_to()/to_edge() before self.add(...)"
                            ),
                        )
                    )

    # If many labels are created and few are positioned, flag density risk.
    unpositioned_labels = [v for v in label_vars if v not in positioned_vars]
    if len(unpositioned_labels) >= 2:
        diagnostics.append(
            _make_diagnostic(
                rule_id="layout.label_overlap_risk",
                severity="warning",
                message=(
                    f"{len(unpositioned_labels)} text/label objects appear unpositioned; "
                    "graph labels may overlap"
                ),
                scene_file=scene_file,
                fix_hint=(
                    "Position each label explicitly with next_to()/move_to() and tune buff spacing"
                ),
            )
        )

    # When both graph and label variables exist, enforce explicit placement for labels.
    if graph_like_vars and label_vars:
        for label_name in sorted(label_vars):
            if label_name not in positioned_vars:
                diagnostics.append(
                    _make_diagnostic(
                        rule_id="layout.graph_label_not_anchored",
                        severity="warning",
                        message=(
                            f"label '{label_name}' is not explicitly anchored relative to graph/axes"
                        ),
                        scene_file=scene_file,
                        fix_hint=(
                            f"Anchor label '{label_name}' using .next_to(<graph_or_axis>, buff=...)"
                        ),
                    )
                )

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
