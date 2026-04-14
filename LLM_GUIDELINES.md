# LLM instructions: using `Manim CLI`

This document tells coding agents and LLM-driven workflows how to use the **manim-cli** harness safely and effectively. Point your system prompt, project rules, or skill loader at this file (or paste a short summary into the agent context).

Every behavioral statement in this document is derived directly from the CLI source. Items that the CLI does **not** yet enforce are explicitly labelled **[authoring guidance — not CLI-enforced]**.

## What this tool is

- A **standalone developer-focused** **Click** CLI around **Manim Community Edition** workflows: discover `Scene` subclasses, analyze Python scene files, validate a repo layout, scaffold a minimal project, and **invoke the real `manim` executable** to render.
- Output is **human text** by default; for agents, always pass **`--json`** (alias: `--json-output`) so responses are **single-document JSON** on stdout.
- **Manim CE alignment:** the harness does not pin Manim. The maintainers record the **last Manim CE version verified** in `manim_cli/manim/_meta.py` (`MANIM_CE_VERIFIED_VERSION`); `manim-cli --version` prints that value for reference only — it is **not** a strict compatibility guarantee.

## Prerequisites (check before promising results)

1. **Install the harness**:

   ```bash
   pip install -e .
   ```

2. **Real renders** require the **`manim`** CLI on `PATH` (Manim CE installed in the same environment). The harness checks via `shutil.which("manim")` before any subprocess call. If `manim` is missing, `render run` returns `ok: false` and `error_code: MANIM_NOT_FOUND`.

3. **`validate repo`** expects a top-level directory named **`manim/`** inside `--repo-path` (Manim CE library clone layout). Arbitrary user projects will fail this check — use `scene list` / `analyze scene-file` for those instead.

---

## JSON Contract (schema v1)

Every `--json` invocation emits **exactly one** JSON object on stdout (`json.dumps`, indent=2, sort_keys=True) with these stable top-level keys:

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
| `VALIDATION_ERROR`             | Missing required layout, invalid argument, or `scene.py` already exists |
| `RENDER_FAILED`                | `manim` subprocess exited non-zero                        |
| `MANIM_NOT_FOUND`              | `manim` binary not on PATH (`shutil.which` returned None) |
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

Pass a JSON file via `--rules-config`. All fields are optional and merge over defaults. The `load_rules` function merges via dataclass field-by-field override; unknown keys are silently ignored.

```jsonc
{
  "schema_version": "1",          // must be "1" if set; any other value raises RULES_LOAD_ERROR
  "policy": "strict",             // "warn" | "strict" | "fix-ready" — use "strict" for LLM-driven work

  "layout": {
    "min_spacing": 0.9,           // stored; passed to template — NOT enforced by policy checks
    "frame_margin": 0.7,          // stored; passed to template — NOT enforced by policy checks
    "overlap_policy": "strict"    // stored — NOT enforced by policy checks
  },

  "color": {
    "approved_palette": ["BLUE", "GOLD", "GREEN", "WHITE", "GREY"],
    // CLI-enforced: any Manim color constant NOT in this list raises color.out_of_palette diagnostic
    // Only enforced when approved_palette is non-empty
    "semantic_mappings": {},       // stored only; not evaluated by any check
    "contrast_threshold": 4.5     // stored only; not evaluated by any check
  },

  "style": {
    "stroke_width": 3.0,          // embedded in project init template; NOT enforced by policy checks
    "fill_opacity": 1.0,          // embedded in project init template
    "font_size": 32,              // embedded in project init template
    "animation_run_time": 1.2
    // CLI-enforced: any explicit run_time= kwarg > 3× this value raises style.animation_run_time diagnostic
  }
}
```

### Default values (when no `--rules-config` is passed)

| Field                        | Default    |
|------------------------------|------------|
| `policy`                     | `"warn"`   |
| `layout.min_spacing`         | `0.5`      |
| `layout.frame_margin`        | `0.5`      |
| `layout.overlap_policy`      | `"warn"`   |
| `color.approved_palette`     | `[]` (no palette check) |
| `color.contrast_threshold`   | `4.5`      |
| `style.stroke_width`         | `2.0`      |
| `style.fill_opacity`         | `1.0`      |
| `style.font_size`            | `24`       |
| `style.animation_run_time`   | `1.0`      |

### Policy modes

| Mode        | Behavior in `validate scene-style` and `render run`              |
|-------------|------------------------------------------------------------------|
| `warn`      | `ok: false` only if `error_count > 0`. Warnings do not block.   |
| `strict`    | `ok: false` if `error_count > 0` OR `warning_count > 0`.        |
| `fix-ready` | Same blocking as `warn`; diagnostics include `fix_hint` fields. |

---

## What the CLI actually checks (policy enforcement reality)

The following two rules are the **only** rules currently enforced by `_run_policy_checks` (used by both `validate scene-style` and the pre-render gate in `render run`):

| `rule_id`                  | Triggered when                                                            | Severity  |
|----------------------------|---------------------------------------------------------------------------|-----------|
| `color.out_of_palette`     | A Manim color constant name is used that is not in `approved_palette`     | `warning` |
| `style.animation_run_time` | An explicit `run_time=` kwarg exceeds `3 × style.animation_run_time`      | `warning` |

`color.out_of_palette` is **only active when `approved_palette` is non-empty**. With an empty palette (the default), no color diagnostics are emitted.

All other fields in `rules.json` (`layout.*`, `color.contrast_threshold`, `style.stroke_width`, `style.font_size`) are stored and embedded into scaffolded templates but are not evaluated by any policy check. Guidance about stroke width, font size, and spacing must be enforced at the **authoring level** by the LLM.

---

## Command reference (agent-oriented)

### `project init`

Creates a `scene.py` file inside `--target-dir` with style constants derived from the active rules.

```text
manim-cli [--rules-config RULES] --json project init \
  --target-dir <DIR> [--scene-name HelloScene]
```

- `--target-dir` is created if it does not exist (`mkdir -p`).
- The generated file is always named **`scene.py`** (not `<scene-name>.py`).
- Returns `ok: false` with `error_code: VALIDATION_ERROR` if `scene.py` already exists in `--target-dir`.

**Returns:** `ok`, `path` (absolute path to written `scene.py`), `scene_name`, `active_rules` (`policy` + `schema_version` only).

The generated `scene.py` embeds `STROKE_WIDTH`, `FONT_SIZE`, `ANIMATION_RUN_TIME`, and `FILL_OPACITY` constants pulled from the active rules, so the template is policy-compliant from the start.

### `scene list`

Recursively scans all `.py` files under `--repo-path` (via `rglob("*.py")`), skipping dotfile directories. Detects any class that directly inherits from `Scene` (checks both `ast.Name` and `ast.Attribute` base forms).

```text
manim-cli --json scene list --repo-path <EXISTING_DIR>
```

- `--repo-path` must exist; Click validates this (`exists=True`).

**Returns:** `ok`, `count`, `scenes[]` (each entry: `name`, `file_path`, `lineno`), `command_args_resolved`.

`scenes[]` is sorted by `(file_path, name)` for determinism. Always use the `file_path` from this output as the value for `--scene-file` in subsequent commands.

### `render run`

Invokes the **real** `manim` binary after running the pre-render policy gate. The render command is built as:

```
manim -q{quality} --renderer={renderer} [--media_dir output_dir] scene_file scene_name
```

```text
manim-cli [--rules-config RULES] --json render run \
  --scene-file <EXISTING_PY> \
  --scene-name <ClassName> \
  [--quality l] \
  [--renderer cairo] \
  [--output-dir <MEDIA_DIR>] \
  [--dry-run]
```

- `--scene-file` must exist (`exists=True`).
- `--quality` defaults to `l` (low); `--renderer` defaults to `cairo`.
- **`--dry-run`**: skips subprocess; returns `ok`, `dry_run: true`, `render_command`, `policy`, `diagnostics[]`. Policy gate still runs.
- The policy gate applies the same two checks as `validate scene-style`. In `strict` mode, any diagnostic (error or warning) sets `ok: false` and `error_code: POLICY_VIOLATION` without invoking `manim`.

**Returns (dry-run):** `ok`, `dry_run`, `render_command`, `policy`, `diagnostics[]`.

**Returns (live render):** `ok`, `render_command`, `returncode`, `stdout`, `stderr`, `output_root`, `policy`, `diagnostics[]`.

> **`command` vs `render_command`**: the envelope `command` field is the CLI subcommand string (`"render run"`). `render_command` inside the payload is the `manim` subprocess argv list.

### `analyze scene-file`

Parses the file with Python's `ast` module and returns a structural summary plus policy-relevant facts for use by LLMs before calling `validate scene-style`.

```text
manim-cli [--rules-config RULES] --json analyze scene-file --scene-file <EXISTING_PY>
```

- `--scene-file` must exist (`exists=True`).

**Returns:** `ok`, `file`, `classes[]`, `class_count`, `policy_facts`.

`classes[]` entries include: `name`, `lineno`, `play_calls[]` (line numbers of `.play()` calls), `mobject_calls[]` (PascalCase constructor calls inside `construct()`).

`policy_facts` fields and what they detect:

| Field                | What the CLI actually detects                                                   |
|----------------------|---------------------------------------------------------------------------------|
| `color_constants`    | Any `ast.Name` node whose `.id` is in the known Manim color constant set        |
| `hex_color_literals` | String literals matching `#` + 6 or 8 hex chars                                |
| `run_time_overrides` | `run_time=<constant>` keyword arguments                                         |
| `add_calls`          | Any `.add(...)` attribute call (not just `self.add`)                            |
| `positioning_calls`  | `.move_to()`, `.shift()`, `.next_to()`, `.to_edge()`, `.to_corner()` calls      |
| `overlap_risk_score` | `max(0, len(add_calls) - len(positioning_calls))` — heuristic only              |

`overlap_risk_score` is a **count heuristic**, not a layout check. It counts all `.add()` calls against all detected positioning calls across the entire file. A score of `0` means there are at least as many positioning calls as add calls — it does not guarantee no overlaps.

### `validate repo`

Checks that `--repo-path` contains a top-level `manim/` package directory (Manim CE library clone layout). Optionally summarizes effective rules.

```text
manim-cli [--rules-config RULES] --json validate repo --repo-path <DIR>
```

**Returns:** `ok`, `errors[]`, `scene_count`, `effective_rules` (when rules are active).

> This command is for Manim CE library clones. For user scene projects, use `scene list` and `analyze scene-file` instead.

### `validate scene-style`

Runs the two active policy checks (see "What the CLI actually checks") on a single scene file.

```text
manim-cli [--rules-config RULES] --json validate scene-style --scene-file <FILE.py>
```

**Returns:** `ok`, `scene_file`, `policy`, `diagnostics[]`, `error_count`, `warning_count`, `effective_rules`.

- `ok: false` always sets `error_code: POLICY_VIOLATION` in the envelope.
- In `strict` mode, `ok: false` if `error_count > 0` OR `warning_count > 0`.
- In `warn` / `fix-ready` mode, `ok: false` only if `error_count > 0`.

Each diagnostic entry:
```jsonc
{
  "rule_id":   "color.out_of_palette",   // "color.out_of_palette" | "style.animation_run_time"
  "severity":  "warning",               // "warning" | "error"
  "message":   "color constant 'RED' is not in the approved palette",
  "location":  { "file": "...", "lineno": 5 },
  "fix_hint":  "Replace with one of: ['BLUE', 'GOLD', 'GREEN', 'GREY', 'WHITE']"
}
```

Diagnostics are sorted by `(rule_id, lineno)` for deterministic agent diffing.

---

## Golden rules for LLMs

1. **Always pass `--json`** so you parse structured output, never table text.
2. **Always pass `--rules-config rules.json`** on every command; active palette and run_time enforcement require it.
3. **Use absolute paths** — Windows paths with spaces must be quoted in shell snippets.
4. **Follow the 5-step pipeline** in order: `scene list` → `analyze scene-file` → `validate scene-style` → `render run --dry-run` → `render run`. No step may be skipped.
5. **Strict mode means stop on any diagnostic**: under `"policy": "strict"`, if `validate scene-style` returns any diagnostic (`error_count > 0` or `warning_count > 0`), fix all before proceeding. Do not attempt dry-run or render.
6. **Check `overlap_risk_score`** in `analyze` output before calling `validate scene-style`. Any value > 0 means fewer positioning calls than add calls — add explicit positioning calls until the score is `0`.
7. **Check `hex_color_literals`** in `analyze` output. Any entry means a hardcoded `#RRGGBB` string — replace with a Manim color constant from the approved palette.
8. **Do not fabricate paths**: derive `--scene-file` from the `file_path` field returned by `scene list`.
9. **`project init` always writes `scene.py`**: the output file is always `<target-dir>/scene.py`. For the multi-module package pattern, rename this file after init.
10. **`command` vs `render_command`**: the envelope `command` field is the CLI subcommand string; `render_command` inside `render run` responses is the manim subprocess argv.
11. **Parse `error_code`** for programmatic branching, not `error` (prose message may change).
12. **Non-interactive mode**: never invoke `manim-cli` without a subcommand in automation — it emits `NON_INTERACTIVE_REPL_BLOCKED` and exits non-zero.

---

## Standardized Development Structure

Every LLM-driven project **must** follow this layout. Do not use a single flat `scene.py` for multi-scene work.

```
project_root/
├── scenes/
│   ├── __init__.py          # empty — marks scenes/ as a package
│   ├── intro_scene.py       # one Scene subclass per file
│   ├── graph_scene.py
│   └── outro_scene.py
├── styles.py                # shared style constants (required)
├── rules.json               # rules config passed to --rules-config
└── media/                   # manim output (--output-dir target)
```

### Module naming conventions

| Module file               | Contains                            |
|---------------------------|-------------------------------------|
| `scenes/<topic>_scene.py` | Exactly one `Scene` subclass        |
| `styles.py`               | All shared style constants          |
| `rules.json`              | Policy config for `--rules-config`  |

- Module files use `snake_case`. Scene class names use `PascalCase` matching the topic (e.g., `graph_scene.py` → `class GraphScene`).
- `styles.py` exports `STROKE_WIDTH`, `FONT_SIZE`, `ANIMATION_RUN_TIME`, `FILL_OPACITY`, and project-wide color assignments. Scene files import from `styles.py`; they do not define their own magic values.
- Never place more than one `Scene` subclass per file. `scene list` scans all `.py` files recursively so multiple classes per file produce ambiguous per-file `validate scene-style` targeting.

### `styles.py` minimum shape

Values here should match your `rules.json` style section so that generated templates and handwritten scenes stay in sync.

```python
# styles.py — import into every scene file
from manim import BLUE, GOLD, GREEN, WHITE, GREY

STROKE_WIDTH       = 3.0
FONT_SIZE          = 32
ANIMATION_RUN_TIME = 1.2
FILL_OPACITY       = 1.0

PRIMARY    = BLUE
SECONDARY  = GOLD
ACCENT     = GREEN
```

### Scaffolding a new scene in the package

`project init` always writes `<target-dir>/scene.py`. Use `--target-dir` pointed at a temp location, then rename the result:

```bash
# Scaffold with rules-compliant constants
manim-cli --json --rules-config rules.json project init \
  --target-dir ./tmp_scaffold --scene-name GraphScene

# Returns: { "ok": true, "path": ".../tmp_scaffold/scene.py", "scene_name": "GraphScene", ... }
# Move the result into the scenes package:
#   mv tmp_scaffold/scene.py scenes/graph_scene.py
# Replace inline constants with: from styles import STROKE_WIDTH, FONT_SIZE, ...
```

---

## Generation + pre-render policy flow

```
manim-cli --rules-config rules.json project init --target-dir ./tmp --scene-name MyScene
  └─ loads rules once
  └─ embeds STROKE_WIDTH, FONT_SIZE, ANIMATION_RUN_TIME, FILL_OPACITY from rules.style

manim-cli --rules-config rules.json analyze scene-file --scene-file scenes/my_scene.py
  └─ AST scan → policy_facts: overlap_risk_score, hex_color_literals, add_calls, positioning_calls

manim-cli --rules-config rules.json validate scene-style --scene-file scenes/my_scene.py
  └─ Checks: color.out_of_palette (if palette defined) + style.animation_run_time (if > 3× default)
  └─ strict → ok: false if any diagnostic (error or warning)
  └─ warn   → ok: false only if error_count > 0
  └─ fix-ready → same as warn; fix_hint provided on each diagnostic

manim-cli --rules-config rules.json render run --scene-file ... --dry-run
  └─ runs same two policy checks before resolving render_command
  └─ strict → blocks on any diagnostic; ok: false + error_code: POLICY_VIOLATION

manim-cli --rules-config rules.json render run --scene-file ...
  └─ same gate, then: manim -q{quality} --renderer={renderer} [--media_dir DIR] FILE CLASS
```

---

## Mandatory Strict Quality Pipeline

This is the **non-negotiable execution contract** for all LLM-driven scene authoring. Every step must complete with `ok: true` before advancing. Under strict policy, any diagnostic in step 3 is a hard stop.

```
Step 1 — Discover
  manim-cli --json scene list --repo-path ./scenes
    └─ Use file_path from scenes[] output as --scene-file in all subsequent commands.
    └─ Never fabricate --scene-file paths.

Step 2 — Analyze
  manim-cli --json --rules-config rules.json analyze scene-file --scene-file <file_path>
    └─ Check policy_facts.overlap_risk_score: if > 0, add positioning calls and re-run step 2.
    └─ Check policy_facts.hex_color_literals: if non-empty, replace with palette constants and re-run step 2.
    └─ Check policy_facts.run_time_overrides: values exceeding 3× animation_run_time will fail step 3.
    └─ Proceed to step 3 only when overlap_risk_score == 0 and hex_color_literals is empty.

Step 3 — Validate style
  manim-cli --json --rules-config rules.json validate scene-style --scene-file <file_path>
    └─ STRICT MODE: ok: false if error_count > 0 OR warning_count > 0 → STOP.
    └─ Apply fix_hint from each diagnostic entry. Re-run steps 2 + 3 after each fix.
    └─ Proceed to step 4 only when ok: true.

Step 4 — Dry-run
  manim-cli --json --rules-config rules.json render run \
    --scene-file <file_path> --scene-name <Class> --quality l --dry-run
    └─ Runs same policy gate; confirms render_command is well-formed.
    └─ If ok: false → parse error_code, fix, restart from step 2.

Step 5 — Render
  manim-cli --json --rules-config rules.json render run \
    --scene-file <file_path> --scene-name <Class> --quality l --output-dir ./media
    └─ Only reached after steps 1–4 all return ok: true.
    └─ On failure: error_code RENDER_FAILED → inspect stderr for Manim/FFmpeg/LaTeX trace.
```

### Error-code retry map

| `error_code`       | Required action before retry                                     |
|--------------------|------------------------------------------------------------------|
| `POLICY_VIOLATION` | Fix all diagnostics from `validate scene-style`; restart step 2 |
| `RENDER_FAILED`    | Read `stderr` in the response; fix Python/Manim error; restart step 2 |
| `FILE_NOT_FOUND`   | Re-run `scene list`; use returned `file_path` exactly           |
| `MANIM_NOT_FOUND`  | Halt; inform user that Manim CE must be installed on PATH        |
| `VALIDATION_ERROR` | Check `--scene-file`/`--scene-name` args; check `scene.py` doesn't already exist for `project init` |
| `RULES_LOAD_ERROR` | Validate `rules.json` against the schema in this document       |

### Recommended `rules.json` for strict graph-heavy projects

```json
{
  "schema_version": "1",
  "policy": "strict",
  "layout": {
    "min_spacing": 0.9,
    "frame_margin": 0.7,
    "overlap_policy": "strict"
  },
  "color": {
    "approved_palette": ["BLUE", "GOLD", "GREEN", "WHITE", "GREY"]
  },
  "style": {
    "stroke_width": 3.0,
    "fill_opacity": 1.0,
    "font_size": 32,
    "animation_run_time": 1.2
  }
}
```

---

## Suggested agent workflows

### A. Scaffold a multi-module project and render with strict policy

```bash
# 1. Scaffold with rules-compliant constants
manim-cli --json --rules-config rules.json project init \
  --target-dir ./tmp_scaffold --scene-name GraphScene
# Returns: { "ok": true, "path": ".../tmp_scaffold/scene.py", ... }
# Move: mv tmp_scaffold/scene.py scenes/graph_scene.py
# Edit: replace inline constants with `from styles import ...`

# 2. Discover — confirm the class appears in scene list
manim-cli --json scene list --repo-path ./scenes
# Use file_path value from scenes[] for all subsequent --scene-file arguments

# 3. Analyze — check overlap_risk_score and hex_color_literals
manim-cli --json --rules-config rules.json analyze scene-file \
  --scene-file ./scenes/graph_scene.py
# If overlap_risk_score > 0: add .move_to()/.next_to()/.shift()/.to_edge()/.to_corner() calls, re-run
# If hex_color_literals non-empty: replace with palette constants, re-run

# 4. Validate style — must return error_count: 0, warning_count: 0
manim-cli --json --rules-config rules.json validate scene-style \
  --scene-file ./scenes/graph_scene.py
# If any diagnostics: apply each fix_hint, then re-run steps 3 + 4

# 5. Dry-run — confirm render_command and that policy gate passes
manim-cli --json --rules-config rules.json render run \
  --scene-file ./scenes/graph_scene.py --scene-name GraphScene \
  --quality l --dry-run

# 6. Render
manim-cli --json --rules-config rules.json render run \
  --scene-file ./scenes/graph_scene.py --scene-name GraphScene \
  --quality l --output-dir ./media
```

### B. Work inside a cloned Manim CE repo

```bash
manim-cli --json validate repo --repo-path <clone>
manim-cli --json scene list --repo-path <clone>
# Use file_path from scene list — do not fabricate paths
manim-cli --json --rules-config rules.json analyze scene-file --scene-file <file_path>
manim-cli --json --rules-config rules.json validate scene-style --scene-file <file_path>
# Only proceed if both steps return ok: true with no diagnostics under strict policy
manim-cli --json --rules-config rules.json render run \
  --scene-file <file_path> --scene-name <Class> --dry-run
manim-cli --json --rules-config rules.json render run \
  --scene-file <file_path> --scene-name <Class> --output-dir ./media
```

### C. Policy-only CI check (strict gate)

```bash
manim-cli --json --rules-config rules.json validate scene-style \
  --scene-file scenes/graph_scene.py
# ok: true + error_count: 0 + warning_count: 0 = clean pass (strict mode)
# ok: false + error_code: POLICY_VIOLATION = blocked; read diagnostics[].fix_hint
```

### D. Fix loop after a policy violation

```bash
# Read diagnostics
manim-cli --json --rules-config rules.json validate scene-style \
  --scene-file scenes/graph_scene.py
# Each diagnostic has: rule_id, severity, location.lineno, fix_hint

# Apply fix_hint instructions to the scene file, then re-analyze
manim-cli --json --rules-config rules.json analyze scene-file \
  --scene-file scenes/graph_scene.py
# Confirm overlap_risk_score == 0 and hex_color_literals is empty

# Re-validate — must reach error_count: 0, warning_count: 0 in strict mode
manim-cli --json --rules-config rules.json validate scene-style \
  --scene-file scenes/graph_scene.py

# Then continue with dry-run and render (workflow A steps 5–6)
```

---

## Graph and Layout Quality Guardrails

Separated into two tiers based on what the CLI enforces vs. what must be handled at the authoring level.

### Tier 1 — CLI-enforced (apply fix_hint from `validate scene-style` output)

| `rule_id`                  | How to fix                                                                 |
|----------------------------|----------------------------------------------------------------------------|
| `color.out_of_palette`     | Replace the color constant with one from `approved_palette` in `rules.json` |
| `style.animation_run_time` | Reduce the `run_time=` kwarg to ≤ 3× `style.animation_run_time` in `rules.json` |

### Tier 2 — Authoring guidance [not CLI-enforced]

These are known causes of visual clutter and overlapping elements. The CLI provides raw data in `analyze` output that LLMs can use to self-check, but no automated diagnostic is raised.

**Overlap and positioning** (use `analyze` output to check):

- `add_calls` count > `positioning_calls` count means some objects have no positioning call at all. Add `.next_to()`, `.move_to()`, `.to_edge()`, `.to_corner()`, or `.shift()` for every text/label object before it is added to the scene.
- The five methods the CLI counts as positioning: `move_to`, `shift`, `next_to`, `to_edge`, `to_corner`.
- Use `buff=` on all `next_to` and `arrange` calls (minimum `buff=0.2`; `buff=0.4` for labels near graph curves).
- Use `VGroup(...).arrange(DOWN, buff=0.3)` for vertical stacks of labels instead of manual `shift` stacking.
- Use `ax.get_graph_label(graph, label, x_val=..., direction=UP)` for graph curve labels instead of manual `MathTex` placement.

**Label density** (max 6 on screen simultaneously):

- No more than 6 text/label objects visible at any one frame. Stage additional labels with `FadeIn`/`FadeOut`.
- Plan the on-screen label set at the top of `construct()` as a comment before writing any code.
- Anchor legends to a frame corner: `legend.to_corner(UL, buff=0.3)`.
- Anchor titles to frame edge: `title.to_edge(UP, buff=0.4)`.

**Line and color clarity** (Manim CE authoring conventions):

- Stroke width for graph curves should be ≥ 3.0 (`STROKE_WIDTH` from `styles.py`). The CLI does not enforce this but embeds the value from `rules.json` into the `project init` template.
- Each plotted line must use a distinct color from `approved_palette`. The CLI will catch out-of-palette constants via `color.out_of_palette`.
- Use `DashedVMobject` to distinguish reference lines from data lines.
- Default text color `WHITE` on `BLACK` background satisfies WCAG AA (≥ 4.5 contrast). The CLI stores `contrast_threshold` but does not evaluate it.

### Pre-render quality checklist

Check these against `analyze scene-file` output before calling `render run --dry-run`:

- [ ] `policy_facts.overlap_risk_score` is `0`
- [ ] `policy_facts.hex_color_literals` is empty
- [ ] `policy_facts.run_time_overrides` values are all ≤ 3× `style.animation_run_time`
- [ ] `validate scene-style` returns `ok: true` (zero diagnostics under strict policy)
- [ ] Max 6 labels on-screen at any one frame (review animation sequence)
- [ ] All `Text`/`MathTex`/`Tex` objects have an explicit position call in `construct()`

---

## Error handling for agents

- Parse **stdout** as JSON when `--json` is set.
- Check `ok` first; if `false`, read `error_code` to branch programmatically, then `error` for prose.
- For `render run`, a failed render still returns JSON with `ok: false`, `error_code: RENDER_FAILED`, and `stderr` containing the Manim/FFmpeg/LaTeX error output.
- If the process exits non-zero and stdout is not JSON, surface **stderr** to the user (missing `manim`, catastrophic import error, etc.).

---

## Agent Prompting and Skill Usage Best Practices

### Scene planning intent (required before writing any code)

Before writing any scene code, the LLM must define and state these four things explicitly:

1. **Layout intent** — what objects are on screen simultaneously and how they are spatially arranged.
2. **Annotation budget** — maximum labels/text objects visible at any one frame (must be ≤ 6).
3. **Color intent** — which approved palette color maps to which data series or element type.
4. **Animation pacing intent** — reveal order and approximate `run_time` per beat (must stay ≤ 3× `style.animation_run_time`).

If any of these four cannot be stated concisely, the scene is too complex for a single module. Split it.

### Do-not rules

- **Do not** render without completing all 5 steps of the Mandatory Strict Quality Pipeline.
- **Do not** use a single `scene.py` for multi-scene work. Use the `scenes/` package structure.
- **Do not** define `STROKE_WIDTH`, `FONT_SIZE`, `ANIMATION_RUN_TIME`, or `FILL_OPACITY` inline in scene files. Import from `styles.py`.
- **Do not** use hex color literals (`#RRGGBB`). Use Manim named constants from the approved palette only. The CLI will detect hex literals in `analyze` output and the `color.out_of_palette` rule will catch unapproved named constants.
- **Do not** call `self.add(obj)` for any text/label object without a preceding explicit position call. The CLI tracks this ratio as `overlap_risk_score`.
- **Do not** continue past a `validate scene-style` result with any diagnostic under strict policy.
- **Do not** fabricate `--scene-file` paths. Derive them from `file_path` in `scene list` output only.
- **Do not** skip `--dry-run`. It runs the same policy gate as `validate scene-style` and confirms the subprocess command before committing.
- **Do not** ignore `overlap_risk_score > 0`. It means there are more `.add()` calls than positioning calls in the file.

### Minimal copy-paste block for system prompts

```text
You have access to manim-cli. Always call it with --json and --rules-config rules.json.

Project structure:
  scenes/<topic>_scene.py  — one Scene subclass per file
  styles.py                — STROKE_WIDTH, FONT_SIZE, ANIMATION_RUN_TIME, FILL_OPACITY, palette constants
  rules.json               — policy: strict; approved_palette defined

CLI enforces two rules (via validate scene-style and pre-render gate):
  color.out_of_palette     — color constant not in approved_palette → warning
  style.animation_run_time — run_time= kwarg > 3× style.animation_run_time → warning
In strict mode, any warning blocks render.

Mandatory pipeline (all steps required, strict order):
  1. Discover:  manim-cli --json scene list --repo-path ./scenes
                → use file_path from scenes[] for all --scene-file args
  2. Analyze:   manim-cli --json --rules-config rules.json analyze scene-file --scene-file <file_path>
                → overlap_risk_score must be 0; hex_color_literals must be empty
  3. Validate:  manim-cli --json --rules-config rules.json validate scene-style --scene-file <file_path>
                → strict: ok: true required (zero diagnostics); apply fix_hint if not
  4. Dry-run:   manim-cli --json --rules-config rules.json render run \
                  --scene-file <file_path> --scene-name <Class> --quality l --dry-run
                → ok: true required before proceeding
  5. Render:    manim-cli --json --rules-config rules.json render run \
                  --scene-file <file_path> --scene-name <Class> --quality l --output-dir ./media

Key response fields:
  ok, schema_version, command, timestamp — always present
  render_command — subprocess argv in render run responses (not command)
  error_code     — machine-readable; branch on this, not on error (prose)
  diagnostics[]  — rule_id, severity, location.lineno, fix_hint

Authoring rules (not CLI-enforced — LLM must apply):
  - Max 6 labels on screen simultaneously
  - All Text/MathTex must have explicit position calls (move_to/next_to/shift/to_edge/to_corner)
  - stroke_width >= 3.0 for graph lines (import STROKE_WIDTH from styles.py)
  - No hex color literals; no out-of-palette constants
  - Import all style constants from styles.py; never define magic values in scene files
```

---

*Entry point: `manim-cli`. Core modules: `manim_cli/manim/cli.py`, `manim_cli/manim/core/rules.py`, `manim_cli/manim/core/analyze.py`, `manim_cli/manim/core/render.py`, `manim_cli/manim/core/validate.py`.*
