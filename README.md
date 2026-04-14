# Manim CLI

Standalone **developer** CLI for [Manim Community Edition](https://www.manim.community/) workflows: discover `Scene` subclasses, analyze scene files, validate a Manim-repo-style tree, scaffold a minimal project, enforce drawing/style policies, and invoke the real `manim` CLI to render.

This package is **not** the Manim library. Install Manim CE separately so `manim` is on your `PATH`.

## Recommended use

- **Audience:** developers and coding agents (structured `--json` output, subprocess-friendly).
- **Install** with [pipx](https://pipx.pypa.io/) so it stays isolated from app projects:

  ```bash
  pipx install manim-cli
  # or from a local clone:
  pip install -e .
  ```

- **Manim CE version note:** the CLI is **not** guaranteed to track every Manim CE release. The **last Manim CE version this repo was verified against** is recorded in `manim_cli/manim/_meta.py` as `MANIM_CE_VERIFIED_VERSION` and shown by:

  ```bash
  manim-cli --version
  ```

## Quick start

```bash
# Scaffold a new project (rule-compliant template)
manim-cli --json project init --target-dir ./my_scene --scene-name MyScene

# Discover scenes
manim-cli --json scene list --repo-path ./my_scene

# Analyze for style/structure
manim-cli --json analyze scene-file --scene-file ./my_scene/scene.py

# Check style policy before rendering
manim-cli --json validate scene-style --scene-file ./my_scene/scene.py

# Dry-run to confirm the manim command
manim-cli --json render run --scene-file ./my_scene/scene.py --scene-name MyScene --dry-run

# Render
manim-cli --json render run --scene-file ./my_scene/scene.py --scene-name MyScene
```

## Global rules config

Pass a JSON rules file to enforce drawing/style policies across all commands:

```bash
manim-cli --json --rules-config rules.json render run \
  --scene-file scene.py --scene-name MyScene
```

Example `rules.json`:

```json
{
  "schema_version": "1",
  "policy": "strict",
  "color": {
    "approved_palette": ["BLUE", "GREEN", "GOLD"]
  },
  "style": {
    "font_size": 32,
    "animation_run_time": 1.5
  }
}
```

Policy modes:

| Mode        | Effect                                                          |
|-------------|-----------------------------------------------------------------|
| `warn`      | Emit diagnostics but proceed (default)                          |
| `strict`    | Block render or validation on any policy violation              |
| `fix-ready` | Emit fix hints; proceed (no blocking)                           |

## Strict-mode example

```bash
# With an out-of-palette color (RED) and strict policy – render is blocked:
manim-cli --json --rules-config rules.json render run \
  --scene-file scene.py --scene-name MyScene --dry-run

# Response includes:
# { "ok": false, "error_code": "POLICY_VIOLATION", "diagnostics": [...] }
```

## Warn-mode example

```bash
manim-cli --json render run \
  --scene-file scene.py --scene-name MyScene --dry-run

# Policy = warn: ok: true even with diagnostics
# { "ok": true, "dry_run": true, "diagnostics": [...], "render_command": [...] }
```

## JSON contract

Every `--json` response has these stable keys: `ok`, `schema_version`, `command`, `timestamp`. On error, `error` and `error_code` are added. See [LLM_GUIDELINES.md](LLM_GUIDELINES.md) for the full contract, error code table, and rules config schema.

## Development

```bash
pip install -e .
python -m pytest tests/ -q
```

## LLM / agent usage

See [LLM_GUIDELINES.md](LLM_GUIDELINES.md) for the complete machine contract, error codes, rules schema, generation and pre-render policy flow, and recommended invocation recipes.
