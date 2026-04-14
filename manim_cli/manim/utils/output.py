from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import click

ENVELOPE_SCHEMA_VERSION = "1"

ERROR_CODES = {
    "FILE_NOT_FOUND",
    "VALIDATION_ERROR",
    "RENDER_FAILED",
    "MANIM_NOT_FOUND",
    "NON_INTERACTIVE_REPL_BLOCKED",
    "RULES_LOAD_ERROR",
    "POLICY_VIOLATION",
    "USAGE_ERROR",
    "UNKNOWN_ERROR",
}


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_envelope(
    ok: bool,
    command: str = "",
    *,
    payload: dict[str, Any] | None = None,
    error: str | None = None,
    error_code: str | None = None,
    details: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Return a single stable JSON response shape for every --json call."""
    envelope: dict[str, Any] = {
        "ok": ok,
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "command": command,
        "timestamp": timestamp or _now_iso(),
    }
    if payload:
        envelope.update(payload)
    if error is not None:
        envelope["error"] = error
    if error_code is not None:
        envelope["error_code"] = error_code
    if details is not None:
        envelope["details"] = details
    return envelope


def build_error_envelope(
    command: str,
    error: str,
    error_code: str = "UNKNOWN_ERROR",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_envelope(
        ok=False,
        command=command,
        error=error,
        error_code=error_code,
        details=details,
    )


def emit(payload: Any, as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, (dict, list)):
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    click.echo(str(payload))
