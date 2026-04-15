from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .rules import GlobalRules, RulesValidationError, default_rules, load_rules
from .scene_index import discover_scenes


def _check_requirements(root: Path) -> dict[str, Any]:
    """Locate a requirements file and check that manim is pinned inside it."""
    req_txt = root / "requirements.txt"
    pyproject = root / "pyproject.toml"

    if req_txt.exists():
        found_file = "requirements.txt"
        content = req_txt.read_text(encoding="utf-8")
        manim_entry: str | None = next(
            (
                line.strip()
                for line in content.splitlines()
                if line.strip().lower().startswith("manim")
            ),
            None,
        )
    elif pyproject.exists():
        found_file = "pyproject.toml"
        content = pyproject.read_text(encoding="utf-8")
        # Coarse check: any line that mentions manim as a dependency token
        manim_entry = next(
            (
                line.strip()
                for line in content.splitlines()
                if "manim" in line.lower() and "=" in line
            ),
            None,
        )
        if manim_entry is None and "manim" in content.lower():
            manim_entry = "manim (referenced in pyproject.toml)"
    else:
        found_file = None
        manim_entry = None

    return {
        "requirements_file": {
            "ok": found_file is not None,
            "found": found_file,
        },
        "manim_pinned": {
            "ok": manim_entry is not None,
            "entry": manim_entry,
        },
    }


def _check_syntax(root: Path) -> dict[str, Any]:
    """Scan all .py files under *root* for syntax errors."""
    errors: list[dict[str, str]] = []
    for py_file in sorted(root.rglob("*.py")):
        if any(part.startswith(".") for part in py_file.parts):
            continue
        try:
            ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError as exc:
            errors.append({"file": str(py_file), "error": str(exc)})
    return {"ok": len(errors) == 0, "files_with_errors": errors}


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
    warnings: list[str] = []
    if not scenes:
        errors.append("no Scene subclasses discovered in repository")

    # Extended checks
    req_checks = _check_requirements(root)
    syntax_check = _check_syntax(root)

    if not req_checks["requirements_file"]["ok"]:
        warnings.append("no requirements.txt or pyproject.toml found")
    elif not req_checks["manim_pinned"]["ok"]:
        warnings.append("manim does not appear to be listed in the requirements file")

    if not syntax_check["ok"]:
        for entry in syntax_check["files_with_errors"]:
            errors.append(f"syntax error in {entry['file']}: {entry['error']}")

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

    checks: dict[str, Any] = {
        "manim_dir": {"ok": True},
        **req_checks,
        "syntax_errors": syntax_check,
    }

    result: dict[str, Any] = {
        "ok": len(errors) == 0 and len(rules_errors) == 0,
        "errors": errors + rules_errors,
        "warnings": warnings,
        "scene_count": len(scenes),
        "checks": checks,
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


def validate_scene_layout(
    scene_file: str,
    rules: GlobalRules | None = None,
) -> dict[str, Any]:
    """Run layout-only checks on a single scene file and return diagnostics."""
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

    diagnostics = [d for d in _run_policy_checks(scene_file, rules) if d["rule_id"].startswith("layout.")]
    errors = [d for d in diagnostics if d["severity"] == "error"]
    warnings = [d for d in diagnostics if d["severity"] == "warning"]

    policy = rules.policy
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
