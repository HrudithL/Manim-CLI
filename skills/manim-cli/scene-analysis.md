# Skill: Scene Analysis Reference

> **Trigger:** When interpreting the output of `analyze scene-file` or deciding whether a scene is ready for validation.

## Command

```bash
manim-cli --json --rules-config rules.json analyze scene-file --scene-file <file_path>
```

## Output structure

```json
{
  "ok": true,
  "file": "<file_path>",
  "classes": [...],
  "class_count": 1,
  "policy_facts": {
    "color_constants": [...],
    "hex_color_literals": [...],
    "run_time_overrides": [...],
    "add_calls": [...],
    "positioning_calls": [...],
    "overlap_risk_score": 0
  }
}
```

## `classes[]` entries

Each entry describes one Scene subclass found in the file:

| Field | Type | Description |
|---|---|---|
| `name` | string | Class name (PascalCase) |
| `lineno` | int | Line number of the class definition |
| `play_calls` | int[] | Line numbers of `.play()` calls in `construct()` |
| `mobject_calls` | string[] | PascalCase constructor calls inside `construct()` |

## `policy_facts` fields

### `color_constants` — list of strings

All Manim color constant names found in the file (e.g. `["BLUE", "RED", "WHITE"]`).

**Action:** Cross-reference with `rules.json` `color.approved_palette`. Any constant not in the palette will trigger `color.out_of_palette` in validation.

### `hex_color_literals` — list of strings

String literals matching `#` + 6 or 8 hex characters (e.g. `["#FF0000"]`).

**Action:** Replace every hex literal with a named Manim constant from the approved palette. Hex literals are always a problem — the CLI cannot validate them against the palette.

**Stop condition:** This list must be empty before proceeding to validation.

### `run_time_overrides` — list of numbers

Explicit `run_time=<constant>` keyword argument values found in the file.

**Action:** Each value must be ≤ 3x `style.animation_run_time` from `rules.json`. If `animation_run_time` is `1.2`, the max is `3.6`. Values exceeding this will trigger `style.animation_run_time` in validation.

### `add_calls` — list of ints

Line numbers of all `.add(...)` attribute calls in the file.

**Action:** Every object added to the scene should have a preceding explicit positioning call. Compare count against `positioning_calls`.

### `positioning_calls` — list of ints

Line numbers of calls to: `move_to()`, `shift()`, `next_to()`, `to_edge()`, `to_corner()`.

**Action:** Count must be ≥ count of `add_calls` to achieve `overlap_risk_score == 0`.

### `overlap_risk_score` — int

Formula: `max(0, len(add_calls) - len(positioning_calls))`

| Value | Meaning | Action |
|---|---|---|
| `0` | At least as many positioning calls as add calls | OK to proceed |
| `> 0` | Some added objects lack positioning | Add explicit position calls, then re-run analysis |

This is a **heuristic**, not a layout check. Score `0` does not guarantee zero overlaps, but score `> 0` reliably indicates missing positioning.

## Pre-validation checklist

Before calling `validate scene-style`, confirm all of:

- [ ] `overlap_risk_score == 0`
- [ ] `hex_color_literals` is empty
- [ ] All `run_time_overrides` values ≤ 3x threshold
- [ ] Max 6 text/label objects visible simultaneously (manual review)
- [ ] All `Text`/`MathTex`/`Tex` objects have explicit positioning in `construct()`
