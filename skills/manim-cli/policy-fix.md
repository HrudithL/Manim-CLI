# Skill: Policy Fix Loop

> **Trigger:** After receiving `error_code: POLICY_VIOLATION` from `validate scene-style` or `render run`.

## Overview

The CLI enforces exactly two policy rules. When either fires, execution is blocked under strict policy. This skill provides the exact fix procedure.

> **Invariant:** After every fix, always re-run `analyze scene-file` before re-running `validate scene-style`. Never skip the re-analyze step.

## Enforced rules

| `rule_id` | Fires when | Severity |
|---|---|---|
| `color.out_of_palette` | A Manim color constant is used that is not in `rules.json` `approved_palette` | `warning` |
| `style.animation_run_time` | An explicit `run_time=` kwarg exceeds 3x `rules.json` `style.animation_run_time` | `warning` |

Under `"policy": "strict"`, any warning blocks rendering.

## Fix procedure

### 1. Read diagnostics

Run `validate scene-style` and parse the `diagnostics[]` array:

```bash
manim-cli --json --rules-config rules.json validate scene-style --scene-file <file_path>
```

Each diagnostic contains:
```json
{
  "rule_id": "color.out_of_palette",
  "severity": "warning",
  "message": "color constant 'RED' is not in the approved palette",
  "location": { "file": "...", "lineno": 5 },
  "fix_hint": "Replace with one of: ['BLUE', 'GOLD', 'GREEN', 'GREY', 'WHITE']"
}
```

### 2. Apply fixes by rule_id

**`color.out_of_palette`:**
- Go to `location.lineno` in the scene file.
- Replace the offending color constant with one from `fix_hint`.
- If the color is a hex literal (`#RRGGBB`), replace with a named Manim constant from the approved palette.

**`style.animation_run_time`:**
- Go to `location.lineno` in the scene file.
- Reduce the `run_time=` value to at most 3x the `style.animation_run_time` from `rules.json`.
- Example: if `animation_run_time` is `1.2`, max allowed `run_time=` is `3.6`.

### 3. Re-analyze

After fixing, always re-run analysis before re-validating:

```bash
manim-cli --json --rules-config rules.json analyze scene-file --scene-file <file_path>
```

Confirm:
- `policy_facts.overlap_risk_score` is `0`
- `policy_facts.hex_color_literals` is `[]`
- `policy_facts.run_time_overrides` all ≤ 3x threshold

### 4. Re-validate

```bash
manim-cli --json --rules-config rules.json validate scene-style --scene-file <file_path>
```

**Stop condition:** `ok: true` with `error_count: 0` and `warning_count: 0`.

If diagnostics remain, repeat from step 2.

### 5. Continue pipeline

Once validation passes, proceed to dry-run (pipeline step 4). See `pipeline.md`.

## Policy modes reference

For policy mode definitions (`strict`, `warn`, `fix-ready`) and their blocking behavior, see `rules-config.md`.

## See Also

| Skill | Purpose |
|---|---|
| `pipeline.md` | Full 5-step render pipeline; policy-fix feeds back into step 2 |
| `scene-analysis.md` | `policy_facts` fields to confirm after each fix |
| `rules-config.md` | Policy mode definitions and `approved_palette` configuration |
