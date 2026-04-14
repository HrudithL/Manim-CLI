from __future__ import annotations

from pathlib import Path
from typing import Any

from .rules import GlobalRules, RulesValidationError, default_rules, load_rules
from .scene_index import discover_scenes


def validate_repo(
    repo_path: str,
    rules: GlobalRules | None = None,
    rules_config_path: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_path)
    if not root.exists():
        return {
            "ok": False,
            "errors": [f"repo path does not exist: {repo_path}"],
            "error_code": "FILE_NOT_FOUND",
        }
    if not (root / "manim").exists():
        return {
            "ok": False,
            "errors": ["expected repo-first layout with top-level `manim/` package"],
            "error_code": "VALIDATION_ERROR",
        }

    scenes = discover_scenes(repo_path)
    errors: list[str] = []
    if not scenes:
        errors.append("no Scene subclasses discovered in repository")

    # Rules config validity check
    rules_summary: dict[str, Any] | None = None
    rules_errors: list[str] = []
    if rules_config_path is not None:
        try:
            loaded = load_rules(rules_config_path)
            rules_summary = loaded.summary()
        except RulesValidationError as exc:
            rules_errors.append(f"rules config invalid: {exc}")
    elif rules is not None:
        rules_summary = rules.summary()

    result: dict[str, Any] = {
        "ok": len(errors) == 0 and len(rules_errors) == 0,
        "errors": errors + rules_errors,
        "scene_count": len(scenes),
    }
    if rules_summary is not None:
        result["effective_rules"] = rules_summary
    return result


def validate_scene_style(
    scene_file: str,
    rules: GlobalRules | None = None,
) -> dict[str, Any]:
    """Run style/policy checks on a single scene file and return diagnostics."""
    from .render import _run_policy_checks  # local import to avoid cycles

    if rules is None:
        rules = default_rules()

    path = Path(scene_file)
    if not path.exists():
        return {
            "ok": False,
            "error": f"scene file does not exist: {scene_file}",
            "error_code": "FILE_NOT_FOUND",
            "diagnostics": [],
        }

    diagnostics = _run_policy_checks(scene_file, rules)
    errors = [d for d in diagnostics if d["severity"] == "error"]
    warnings = [d for d in diagnostics if d["severity"] == "warning"]

    policy = rules.policy
    violations: int
    if policy == "strict":
        violations = len(errors) + len(warnings)
    else:
        violations = len(errors)

    return {
        "ok": violations == 0,
        "scene_file": scene_file,
        "policy": policy,
        "diagnostics": diagnostics,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "effective_rules": rules.summary(),
    }
