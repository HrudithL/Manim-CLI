# Skill: Mandatory Render Pipeline

> **Trigger:** Before rendering any Manim scene. Execute all 6 steps in order; never skip a step.

## Step 1 — Discover scenes

```bash
manim-cli --json scene list --repo-path ./scenes
```

**Check:** `ok: true`. Use `scenes[].file_path` as `--scene-file` in all later steps.
Never fabricate paths — always derive from this output.

**Fields:** `count`, `scenes[]` (each: `name`, `file_path`, `lineno`).

## Step 2 — Analyze

```bash
manim-cli --json --rules-config rules.json analyze scene-file --scene-file <file_path>
```

See `scene-analysis.md` for a full description of every `policy_facts` field and what each value means.

**Stop conditions — all must pass before proceeding:**

| Field | Required value | Action if violated |
|---|---|---|
| `policy_facts.overlap_risk_score` | `0` | Add `move_to`/`next_to`/`shift`/`to_edge`/`to_corner` calls, then re-run step 2 |
| `policy_facts.hex_color_literals` | `[]` (empty) | Replace every hex literal with a named Manim constant from the approved palette, then re-run step 2 |
| `policy_facts.run_time_overrides` | All values ≤ 3x `style.animation_run_time` | Reduce `run_time=` kwargs to at most 3x threshold, then re-run step 2 |

## Step 3 — Validate style

```bash
manim-cli --json --rules-config rules.json validate scene-style --scene-file <file_path>
```

**Check:** `ok: true` with `error_count: 0` and `warning_count: 0` (strict mode).

If `ok: false`: read `diagnostics[].fix_hint`, apply each fix, then re-run `analyze scene-file` (step 2), confirm all `policy_facts` stop conditions pass, then re-run `validate scene-style` (step 3).
See `policy-fix.md` for the full fix loop.

**Fields:** `diagnostics[]` (each: `rule_id`, `severity`, `message`, `location.lineno`, `fix_hint`).

## Step 4 — Validate layout

```bash
manim-cli --json --rules-config rules.json validate scene-layout --scene-file <file_path>
```

**Check:** `ok: true` with `error_count: 0` and `warning_count: 0` (strict mode).

If `ok: false`: read `diagnostics[].fix_hint`, apply each fix, then re-run `analyze scene-file` (step 2), `validate scene-style` (step 3), then this step.
See `validator.md` for rule IDs and fix guidance.

**Fields:** `diagnostics[]` (each: `rule_id`, `severity`, `message`, `location.lineno`, `fix_hint`).

## Step 5 — Dry-run

```bash
manim-cli --json --rules-config rules.json render run \
  --scene-file <file_path> --scene-name <ClassName> --quality l --dry-run
```

**Check:** `ok: true`. Confirms `render_command` is well-formed and policy gate passes.

If `ok: false`: parse `error_code`, fix, restart from step 2.

**Fields:** `dry_run: true`, `render_command` (subprocess argv), `policy`, `diagnostics[]`.

## Step 6 — Render

```bash
manim-cli --json --rules-config rules.json render run \
  --scene-file <file_path> --scene-name <ClassName> --quality l --output-dir ./media
```

**Check:** `ok: true`, `returncode: 0`.

If `error_code: MANIM_NOT_FOUND`: **Halt** — inform the user that Manim CE must be installed and on PATH before proceeding.

If `error_code: RENDER_FAILED`: read `stderr` for Manim/FFmpeg/LaTeX trace, fix, restart from step 2.

**Fields:** `render_command`, `returncode`, `stdout`, `stderr`, `output_root`.

## Error-code retry map

| `error_code` | Action |
|---|---|
| `POLICY_VIOLATION` | Fix diagnostics → restart step 2 |
| `RENDER_FAILED` | Read `stderr` → fix Python/Manim error → restart step 2 |
| `FILE_NOT_FOUND` | Re-run step 1 → use returned `file_path` |
| `MANIM_NOT_FOUND` | Halt — inform user Manim CE must be installed |
| `VALIDATION_ERROR` | Check `--scene-file` / `--scene-name` args |
| `RULES_LOAD_ERROR` | Validate `rules.json` against schema (see `rules-config.md`) |
| `NON_INTERACTIVE_REPL_BLOCKED` | A subcommand was omitted — always provide a full subcommand in `--json` mode |
| `UNKNOWN_ERROR` | Unexpected runtime exception — report full JSON output to user |

## See Also

| Skill | Purpose |
|---|---|
| `scene-analysis.md` | Full `policy_facts` field reference for step 2 |
| `validator.md` | Mandatory layout gate and `layout.*` diagnostics |
| `policy-fix.md` | Detailed fix loop for `POLICY_VIOLATION` |
| `rules-config.md` | `rules.json` schema and policy mode definitions |
| `ci-gate.md` | Validation-only pipeline for CI / pre-commit |
| `project-init.md` | Scaffold scenes before running the pipeline |
