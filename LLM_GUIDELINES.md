# LLM instructions: using `Manim CLI`

This document tells coding agents and LLM-driven workflows how to use the **manim-cli** harness safely and effectively. Point your system prompt, project rules, or skill loader at this file (or paste a short summary into the agent context).

## What this tool is

- A **standalone developer-focused** **Click** CLI around **Manim Community Edition** workflows: discover `Scene` subclasses, analyze Python scene files, validate a repo layout, scaffold a minimal project, and **invoke the real `manim` executable** to render.
- Output is **human text** by default; for agents, always pass **`--json`** (alias: `--json-output`) so responses are **single-document JSON** on stdout.
- **Manim CE alignment:** the harness does not pin Manim. The maintainers record the **last Manim CE version verified** in `manim_cli/manim/_meta.py` (`MANIM_CE_VERIFIED_VERSION`); `manim-cli --version` prints that value for reference only — it is **not** a strict compatibility guarantee.

## Prerequisites (check before promising results)

1. **Install the harness**:

   ```bash
   pip install -e .
   ```

2. **Real renders** require the **`manim`** CLI on `PATH` (Manim CE installed in the same environment). If `manim` is missing, `render run` returns JSON with `ok: false` and `error_code: MANIM_NOT_FOUND`.

3. **`validate repo`** expects a **clone of [ManimCommunity/manim](https://github.com/ManimCommunity/manim)**-style layout: a top-level directory named **`manim/`** (the library package). Arbitrary user projects may fail validation even if they are valid Manim projects — use `scene list` / `analyze` for those.

---

## JSON Contract (schema v1)

Every `--json` invocation emits **exactly one** JSON object on stdout with these stable top-level keys:

| Key              | Type    | Always present | Description                                              |
|------------------|---------|---------------|----------------------------------------------------------|
| `ok`             | bool    | yes           | `true` on success, `false` on any failure                |
| `schema_version` | string  | yes           | Response contract version (`"1"`)                        |
| `command`        | string  | yes           | CLI subcommand that produced this response               |
| `timestamp`      | string  | yes           | UTC ISO-8601 timestamp (`YYYY-MM-DDTHH:MM:SSZ`)          |
| `error`          | string  | on failure    | Human-readable error message                             |
| `error_code`     | string  | on failure    | Machine-readable error code (see table below)            |
| `details`        | object  | optional      | Structured extra context for the error                   |

### Error codes

| Code                           | Triggered by                                              |
|--------------------------------|-----------------------------------------------------------|
| `FILE_NOT_FOUND`               | Scene file or repo path does not exist                    |
| `VALIDATION_ERROR`             | Missing required layout, invalid argument                 |
| `RENDER_FAILED`                | `manim` subprocess exited non-zero                        |
| `MANIM_NOT_FOUND`              | `manim` binary not on PATH                                |
| `NON_INTERACTIVE_REPL_BLOCKED` | No subcommand provided in non-interactive / `--json` mode |
| `RULES_LOAD_ERROR`             | Rules config file missing, invalid JSON, or fails schema  |
| `POLICY_VIOLATION`             | Pre-render or style gate blocked execution                |
| `USAGE_ERROR`                  | Click usage / missing required option                     |
| `UNKNOWN_ERROR`                | Unexpected runtime exception                              |

---

## Global options

| Flag                       | Meaning                                                        |
|----------------------------|----------------------------------------------------------------|
| `--json` / `--json-output` | Emit structured JSON for the subcommand (required for agents). |
| `--rules-config PATH`      | Path to a JSON rules config file (loaded once, applied everywhere). |
| `-h` / `--help`            | Standard help.                                                 |

---

## Rules config schema (v1)

Pass a JSON file via `--rules-config`. All fields are optional and merge over defaults.

```jsonc
{
  "schema_version": "1",          // must be "1" if set
  "policy": "warn",               // "warn" | "strict" | "fix-ready"

  "layout": {
    "min_spacing": 0.5,           // minimum gap between mobjects
    "frame_margin": 0.5,          // margin from frame edges
    "overlap_policy": "warn"      // "warn" | "strict"
  },

  "color": {
    "approved_palette": [],        // list of Manim color constant names e.g. ["BLUE","GREEN"]
    "semantic_mappings": {},       // { "primary": "BLUE", "accent": "GOLD" }
    "contrast_threshold": 4.5     // WCAG contrast ratio threshold
  },

  "style": {
    "stroke_width": 2.0,
    "fill_opacity": 1.0,
    "font_size": 24,
    "animation_run_time": 1.0
  }
}
```

### Policy modes

| Mode        | Behavior                                                         |
|-------------|------------------------------------------------------------------|
| `warn`      | Emit diagnostics; proceed (generation/render not blocked).       |
| `strict`    | Block render/validation if any diagnostic (error or warning).    |
| `fix-ready` | Emit structured fix hints; proceed (diagnostics only, no block). |

---

## Command reference (agent-oriented)

### `project init`

Create a minimal `scene.py` with rule-compliant style constants.

```text
manim-cli [--rules-config RULES] --json project init \
  --target-dir <DIR> [--scene-name HelloScene]
```

Returns: `ok`, `path`, `scene_name`, `active_rules` (policy + schema_version).

The generated `scene.py` includes `STROKE_WIDTH`, `FONT_SIZE`, `ANIMATION_RUN_TIME`, and `FILL_OPACITY` constants derived from the active rules, preventing ad-hoc magic values.

### `scene list`

Scan a directory tree for classes that inherit from `Scene`.

```text
manim-cli --json scene list --repo-path <EXISTING_DIR>
```

Returns: `ok`, `count`, `scenes[]` (name, file_path, lineno) — sorted by `(file_path, name)` for determinism.

### `render run`

Invoke **real** Manim after running the pre-render policy gate.

```text
manim-cli [--rules-config RULES] --json render run \
  --scene-file <EXISTING_PY> \
  --scene-name <ClassName> \
  [--quality l] \
  [--renderer cairo] \
  [--output-dir <MEDIA_DIR>] \
  [--dry-run]
```

- **`--dry-run`**: does not invoke `manim`; returns `ok`, `render_command`, `diagnostics`, `policy`.
- **`render_command`**: the resolved subprocess argv array (not `command` — that is the CLI subcommand).
- Policy gate runs before any subprocess execution. In `strict` mode any diagnostic blocks the render.

### `analyze scene-file`

Lightweight AST summary plus policy-relevant facts.

```text
manim-cli [--rules-config RULES] --json analyze scene-file --scene-file <EXISTING_PY>
```

Returns: `ok`, `file`, `classes[]`, `class_count`, `policy_facts`.

`policy_facts` includes:
- `color_constants` — Manim color name references with line numbers
- `hex_color_literals` — `#RRGGBB` string literals
- `run_time_overrides` — explicit `run_time=` keyword args
- `add_calls` — `self.add(...)` calls (overlap risk indicator)
- `positioning_calls` — positioning method calls (`.move_to`, `.shift`, `.next_to`, etc.)
- `overlap_risk_score` — heuristic: `max(0, add_calls - positioning_calls)`

### `validate repo`

Check that a path is a valid Manim-CE-style repo layout, and optionally include rules policy summary.

```text
manim-cli [--rules-config RULES] --json validate repo --repo-path <DIR>
```

Returns: `ok`, `errors[]`, `scene_count`, and `effective_rules` (when rules are active).

### `validate scene-style`

Run style/policy diagnostics on a single scene file.

```text
manim-cli [--rules-config RULES] --json validate scene-style --scene-file <FILE.py>
```

Returns: `ok`, `scene_file`, `policy`, `diagnostics[]`, `error_count`, `warning_count`, `effective_rules`.

Each diagnostic entry has stable machine-readable fields:
```jsonc
{
  "rule_id":   "color.out_of_palette",   // stable identifier
  "severity":  "warning",               // "warning" | "error"
  "message":   "color constant 'RED' ...",
  "location":  { "file": "...", "lineno": 5 },
  "fix_hint":  "Replace with one of: ['BLUE']"  // only when available
}
```

Diagnostics are **sorted** by `(rule_id, lineno)` for deterministic agent diffing.

---

## Golden rules for LLMs

1. **Always pass `--json`** so you parse structured output, never table text.
2. **Use absolute paths** — Windows paths with spaces must be quoted in shell snippets.
3. **Pass `--rules-config`** when operating in policy-enforced contexts.
4. **Discover before rendering**: `scene list` → pick `name` and `file_path` → `render run`.
5. **Dry-run first**: `render run --dry-run` validates the command and runs policy checks before committing to a full render.
6. **Do not fabricate paths**: `--scene-file` and `--repo-path` must exist.
7. **`command` vs `render_command`**: the envelope `command` field is the CLI subcommand string; `render_command` inside `render run` responses is the manim subprocess argv.
8. **Parse `error_code`** for programmatic branching, not `error` (prose message may change).
9. **Non-interactive mode**: never invoke `manim-cli` without a subcommand in automation — it emits `NON_INTERACTIVE_REPL_BLOCKED` and exits non-zero.

---

## Generation + pre-render policy flow

```
manim-cli --rules-config rules.json project init --target-dir ./my_scene
  └─ loads rules once
  └─ embeds STROKE_WIDTH, FONT_SIZE, ANIMATION_RUN_TIME, FILL_OPACITY constants

manim-cli --rules-config rules.json validate scene-style --scene-file my_scene/scene.py
  └─ AST-based policy check → diagnostics with rule_id, severity, location, fix_hint

manim-cli --rules-config rules.json render run --scene-file ... --dry-run
  └─ pre-render gate: warn → proceed with diagnostics
                      strict → block if any diagnostic
                      fix-ready → proceed with fix_hint suggestions

manim-cli --rules-config rules.json render run --scene-file ...
  └─ same gate, then invokes manim subprocess
```

---

## Suggested agent workflows

### A. Scaffold and render with policy

```bash
manim-cli --json --rules-config rules.json project init --target-dir ./proj --scene-name MyScene
# edit proj/scene.py
manim-cli --json --rules-config rules.json validate scene-style --scene-file proj/scene.py
manim-cli --json --rules-config rules.json render run --scene-file proj/scene.py --scene-name MyScene --dry-run
manim-cli --json --rules-config rules.json render run --scene-file proj/scene.py --scene-name MyScene
```

### B. Work inside a cloned Manim CE repo

```bash
manim-cli --json validate repo --repo-path <clone>
manim-cli --json scene list --repo-path <clone>
manim-cli --json analyze scene-file --scene-file <file>
manim-cli --json render run --scene-file <file> --scene-name <Class> --dry-run
manim-cli --json render run --scene-file <file> --scene-name <Class>
```

### C. Policy-only CI check

```bash
manim-cli --json --rules-config rules.json validate scene-style --scene-file scene.py
# Exit 0 = ok (or ok with warnings in warn/fix-ready mode)
# Exit non-zero + error_code POLICY_VIOLATION = strict gate failed
```

---

## Error handling for agents

- Parse **stdout** as JSON when `--json` is set.
- Check `ok` first; if `false`, read `error_code` to branch programmatically, then `error` for prose.
- For `render run`, a failed render still returns JSON with `ok: false` and `error_code: RENDER_FAILED`; inspect `stderr` for LaTeX, FFmpeg, or Manim tracebacks.
- If the process exits non-zero and stdout is not JSON, surface **stderr** to the user (missing `manim`, catastrophic import error, etc.).

---

## Minimal copy-paste block for system prompts

```text
You have access to manim-cli. Always call it with --json.
Discover scenes: manim-cli --json scene list --repo-path <DIR>
Analyze file:    manim-cli --json analyze scene-file --scene-file <FILE.py>
Style check:     manim-cli --json validate scene-style --scene-file <FILE.py>
Render (check):  manim-cli --json render run --scene-file <FILE.py> --scene-name <Class> --dry-run
Render:          manim-cli --json render run --scene-file <FILE.py> --scene-name <Class>
Validate repo:   manim-cli --json validate repo --repo-path <DIR>
Global rules:    add --rules-config <rules.json> to any command for policy enforcement.
Key: envelope has ok, schema_version, command, timestamp on every response.
     render run uses render_command (not command) for the subprocess argv.
     error_code is machine-readable; error is human-readable prose.
```

---

*Entry point: `manim-cli`. Core modules: `manim_cli/manim/cli.py`, `manim_cli/manim/core/rules.py`.*
