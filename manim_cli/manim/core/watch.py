"""File-watch loop for continuous scene validation."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Generator

from .render import _run_policy_checks
from .rules import GlobalRules


def watch_scene_file(
    scene_file: str,
    rules: GlobalRules,
    poll_interval: float = 1.0,
) -> Generator[dict[str, Any], None, None]:
    """Poll *scene_file* every *poll_interval* seconds and yield a validation
    result dict each time the file content changes.

    The first result is emitted immediately (current file state on entry).
    Yields nothing while the file is absent; resumes when it reappears.
    Raises ``KeyboardInterrupt`` to the caller on Ctrl-C.
    """
    path = Path(scene_file)
    last_mtime: float | None = None

    while True:
        try:
            current_mtime = path.stat().st_mtime
        except FileNotFoundError:
            current_mtime = None

        if current_mtime != last_mtime:
            last_mtime = current_mtime
            if current_mtime is not None:
                yield _validate(scene_file, rules)

        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _validate(scene_file: str, rules: GlobalRules) -> dict[str, Any]:
    diagnostics = _run_policy_checks(scene_file, rules)
    errors = [d for d in diagnostics if d["severity"] == "error"]
    warnings = [d for d in diagnostics if d["severity"] == "warning"]

    policy = rules.policy
    if policy == "strict":
        violations = len(errors) + len(warnings)
    else:
        violations = len(errors)

    return {
        "scene_file": scene_file,
        "ok": violations == 0,
        "policy": policy,
        "diagnostics": diagnostics,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
