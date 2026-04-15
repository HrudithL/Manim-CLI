"""Auto-fix engine for fixable policy diagnostics.

Fixable rules
-------------
color.out_of_palette      Replace the named color with the first approved
                          palette color (word-boundary substitution on the
                          diagnostic line).
style.animation_run_time  Cap the run_time literal to the threshold value
                          extracted from the diagnostic's fix_hint.

All other rules (layout.*) require structural code changes and are left as
unfixed diagnostics with their fix_hint intact.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .render import _run_policy_checks
from .rules import GlobalRules, default_rules

# Rules this engine can patch automatically
_FIXABLE_RULE_IDS = frozenset(["color.out_of_palette", "style.animation_run_time"])


# ---------------------------------------------------------------------------
# Line-level patchers
# ---------------------------------------------------------------------------

def _patch_color(line: str, color_name: str, replacement: str) -> str:
    """Replace *color_name* with *replacement* using word-boundary matching."""
    return re.sub(rf"\b{re.escape(color_name)}\b", replacement, line)


def _patch_run_time(line: str, threshold: float) -> str:
    """Replace the numeric value of run_time=<N> with *threshold*."""
    return re.sub(
        r"(run_time\s*=\s*)([\d.]+)",
        lambda m: f"{m.group(1)}{threshold}",
        line,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_fixes(
    scene_file: str,
    rules: GlobalRules | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Apply auto-fixes for fixable diagnostics in *scene_file*.

    Parameters
    ----------
    scene_file:
        Path to the Python scene file to patch.
    rules:
        Active GlobalRules; defaults to ``default_rules()``.
    dry_run:
        When True, compute fixes but do not write the file.

    Returns a result dict with:
    - ``fixes_applied``: list of applied (or would-be-applied) patches
    - ``unfixed_diagnostics``: diagnostics that require manual intervention
    - ``ok``: True unless the file was not found
    """
    if rules is None:
        rules = default_rules()

    path = Path(scene_file)
    if not path.exists():
        return {
            "ok": False,
            "error": f"scene file does not exist: {scene_file}",
            "error_code": "FILE_NOT_FOUND",
            "fixes_applied": [],
            "unfixed_diagnostics": [],
        }

    diagnostics = _run_policy_checks(scene_file, rules)
    fixable = [d for d in diagnostics if d["rule_id"] in _FIXABLE_RULE_IDS]
    unfixable = [d for d in diagnostics if d["rule_id"] not in _FIXABLE_RULE_IDS]

    if not fixable:
        return {
            "ok": True,
            "scene_file": scene_file,
            "dry_run": dry_run,
            "fixes_applied": [],
            "fix_count": 0,
            "unfixed_diagnostics": unfixable,
            "unfixed_count": len(unfixable),
        }

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    fixes_applied: list[dict[str, Any]] = []

    # Group fixable diagnostics by line number; skip those without a location.
    by_line: dict[int, list[dict[str, Any]]] = defaultdict(list)
    no_location: list[dict[str, Any]] = []
    for d in fixable:
        lineno = d.get("location", {}).get("lineno")
        if lineno is not None:
            by_line[lineno].append(d)
        else:
            no_location.append(d)

    # Process in reverse order so earlier line numbers stay valid.
    for lineno in sorted(by_line.keys(), reverse=True):
        idx = lineno - 1
        if idx < 0 or idx >= len(lines):
            continue

        original = lines[idx]
        modified = original

        for diag in by_line[lineno]:
            rule_id = diag["rule_id"]

            if rule_id == "color.out_of_palette":
                m = re.search(r"color constant '(\w+)'", diag["message"])
                approved = sorted(rules.color.approved_palette)
                if m and approved:
                    color_name = m.group(1)
                    replacement = approved[0]
                    patched = _patch_color(modified, color_name, replacement)
                    if patched != modified:
                        fixes_applied.append(
                            {
                                "rule_id": rule_id,
                                "lineno": lineno,
                                "description": f"replaced '{color_name}' with '{replacement}'",
                            }
                        )
                        modified = patched

            elif rule_id == "style.animation_run_time":
                hint = diag.get("fix_hint", "")
                m = re.search(r"run_time\s*<=\s*([\d.]+)", hint)
                if m:
                    threshold = float(m.group(1))
                    patched = _patch_run_time(modified, threshold)
                    if patched != modified:
                        fixes_applied.append(
                            {
                                "rule_id": rule_id,
                                "lineno": lineno,
                                "description": f"capped run_time to {threshold}",
                            }
                        )
                        modified = patched

        lines[idx] = modified

    if not dry_run and fixes_applied:
        path.write_text("".join(lines), encoding="utf-8")

    # Diagnostics we couldn't resolve (no location or unfixable rule)
    remaining_unfixed = unfixable + no_location

    return {
        "ok": True,
        "scene_file": scene_file,
        "dry_run": dry_run,
        "fixes_applied": fixes_applied,
        "fix_count": len(fixes_applied),
        "unfixed_diagnostics": remaining_unfixed,
        "unfixed_count": len(remaining_unfixed),
    }
