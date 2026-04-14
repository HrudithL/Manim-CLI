# Skill: Mandatory Render Pipeline

> **Trigger:** Before rendering any Manim scene. Execute all 5 steps in order; never skip a step.

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

**Stop conditions — all must pass before proceeding:**

| Field | Required value | If violated |
|---|---|---|
| `policy_facts.overlap_risk_score` | `0` | Add positioning calls (`move_to`, `next_to`, `shift`, `to_edge`, `to_corner`) then re-run step 2 |
| `policy_facts.hex_color_literals` | `[]` (empty) | Replace hex strings with Manim palette constants then re-run step 2 |
| `policy_facts.run_time_overrides` | All values ≤ 3x `style.animation_run_time` | Reduce `run_time=` kwargs then re-run step 2 |

## Step 3 — Validate style

```bash
manim-cli --json --rules-config rules.json validate scene-style --scene-file <file_path>
```

**Check:** `ok: true` with `error_count: 0` and `warning_count: 0` (strict mode).

If `ok: false`: read `diagnostics[].fix_hint`, apply each fix, then restart from step 2.
See `policy-fix.md` for the full fix loop.

**Fields:** `diagnostics[]` (each: `rule_id`, `severity`, `message`, `location.lineno`, `fix_hint`).

## Step 4 — Dry-run

```bash
manim-cli --json --rules-config rules.json render run \
  --scene-file <file_path> --scene-name <ClassName> --quality l --dry-run
```

**Check:** `ok: true`. Confirms `render_command` is well-formed and policy gate passes.

If `ok: false`: parse `error_code`, fix, restart from step 2.

**Fields:** `dry_run: true`, `render_command` (subprocess argv), `policy`, `diagnostics[]`.

## Step 5 — Render

```bash
manim-cli --json --rules-config rules.json render run \
  --scene-file <file_path> --scene-name <ClassName> --quality l --output-dir ./media
```

**Check:** `ok: true`, `returncode: 0`.

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
