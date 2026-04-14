# Manim CLI — Agent Skills Index

> **Trigger:** Load this skill at the start of any session that uses `manim-cli`.

## Available skills

| Skill file | When to load |
|---|---|
| `pipeline.md` | Before rendering any scene (the mandatory 5-step pipeline) |
| `project-init.md` | When scaffolding a new Manim project or adding a scene module |
| `policy-fix.md` | After any `POLICY_VIOLATION` error code |
| `scene-analysis.md` | When interpreting `analyze scene-file` output fields |
| `ci-gate.md` | When running validation-only checks in CI or pre-commit |
| `rules-config.md` | When creating or editing `rules.json` |

## Quick reference — global flags

Every `manim-cli` invocation in an agent context **must** include:

```bash
manim-cli --json --rules-config rules.json <subcommand>
```

- `--json` — structured JSON on stdout; parse `ok` first, then `error_code` for failures.
- `--rules-config rules.json` — load policy, color palette, and style thresholds.

## Minimal system-prompt block

Paste this into an agent's system prompt for baseline operation:

```text
You have access to manim-cli. Always use --json and --rules-config rules.json.

Project layout:
  scenes/<topic>_scene.py — one Scene subclass per file
  styles.py — shared constants: STROKE_WIDTH, FONT_SIZE, ANIMATION_RUN_TIME, FILL_OPACITY
  rules.json — policy: strict; approved_palette defined

Mandatory pipeline (strict order, all steps required):
  1. scene list  →  2. analyze scene-file  →  3. validate scene-style
  4. render run --dry-run  →  5. render run

Key JSON fields: ok, error_code, diagnostics[], render_command
```

## JSON envelope contract

Every `--json` response contains these top-level fields:

| Field | Type | Always present | Purpose |
|---|---|---|---|
| `ok` | bool | yes | `true` on success |
| `schema_version` | string | yes | `"1"` |
| `command` | string | yes | CLI subcommand name |
| `timestamp` | string | yes | UTC ISO-8601 |
| `error` | string | on failure | Human-readable message |
| `error_code` | string | on failure | Machine-readable — branch on this |

## Error codes

| Code | Meaning |
|---|---|
| `FILE_NOT_FOUND` | Path does not exist |
| `VALIDATION_ERROR` | Bad argument or file already exists |
| `RENDER_FAILED` | Manim subprocess exited non-zero |
| `MANIM_NOT_FOUND` | `manim` binary not on PATH |
| `POLICY_VIOLATION` | Style/color gate blocked execution |
| `RULES_LOAD_ERROR` | Invalid rules.json |
| `USAGE_ERROR` | Missing required CLI option |
| `NON_INTERACTIVE_REPL_BLOCKED` | No subcommand provided in `--json` / non-interactive mode |
| `UNKNOWN_ERROR` | Unexpected runtime exception |

## See Also

| Skill | Purpose |
|---|---|
| `pipeline.md` | Mandatory 5-step render pipeline with error-code retry map |
| `project-init.md` | Scaffold a new project or add a scene module |
| `policy-fix.md` | Fix loop after `POLICY_VIOLATION` |
| `scene-analysis.md` | Full reference for `analyze scene-file` output fields |
| `ci-gate.md` | Batch validation scripts for CI / pre-commit |
| `rules-config.md` | `rules.json` schema, defaults, and `styles.py` sync table |
