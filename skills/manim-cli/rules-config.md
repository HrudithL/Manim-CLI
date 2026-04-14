# Skill: Rules Configuration Reference

> **Trigger:** When creating, editing, or troubleshooting `rules.json`.

## Schema (version 1)

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
    "approved_palette": ["BLUE", "GOLD", "GREEN", "WHITE", "GREY"],
    "semantic_mappings": {},
    "contrast_threshold": 4.5
  },
  "style": {
    "stroke_width": 3.0,
    "fill_opacity": 1.0,
    "font_size": 32,
    "animation_run_time": 1.2
  }
}
```

## Field enforcement status

Fields marked **CLI-enforced** trigger diagnostics in `validate scene-style` and the `render run` pre-gate. Fields marked **stored only** are available in `analyze` output or embedded in scaffolded templates but have no automated check.

| Field | Default | CLI-enforced? |
|---|---|---|
| `policy` | `"warn"` | Yes — controls blocking behavior |
| `color.approved_palette` | `[]` | Yes — when non-empty, triggers `color.out_of_palette` |
| `style.animation_run_time` | `1.0` | Yes — `run_time=` kwargs > 3x this value trigger `style.animation_run_time` |
| `layout.min_spacing` | `0.5` | No — stored, passed to template |
| `layout.frame_margin` | `0.5` | No — stored, passed to template |
| `layout.overlap_policy` | `"warn"` | No — stored only |
| `color.semantic_mappings` | `{}` | No — stored only |
| `color.contrast_threshold` | `4.5` | No — stored only |
| `style.stroke_width` | `2.0` | No — embedded in `project init` template |
| `style.fill_opacity` | `1.0` | No — embedded in `project init` template |
| `style.font_size` | `24` | No — embedded in `project init` template |

## Policy modes

| Mode | Behavior |
|---|---|
| `"warn"` | `ok: false` only when `error_count > 0`. Warnings do not block. |
| `"strict"` | `ok: false` when `error_count > 0` OR `warning_count > 0`. Use for agent-driven work. |
| `"fix-ready"` | Same blocking as `"warn"`. Diagnostics include `fix_hint` fields. |

## Loading rules

Pass via `--rules-config` on every invocation:

```bash
manim-cli --json --rules-config rules.json <subcommand>
```

- `schema_version` must be `"1"` if set; any other value raises `RULES_LOAD_ERROR`.
- Unknown keys are silently ignored.
- All fields are optional and merge over defaults.

## Keeping styles.py in sync

Values in `styles.py` must match the corresponding `rules.json` fields:

| `rules.json` field | `styles.py` constant |
|---|---|
| `style.stroke_width` | `STROKE_WIDTH` |
| `style.font_size` | `FONT_SIZE` |
| `style.animation_run_time` | `ANIMATION_RUN_TIME` |
| `style.fill_opacity` | `FILL_OPACITY` |
| `color.approved_palette` | Color imports + semantic aliases |

## Recommended configs

### Strict graph-heavy project

```json
{
  "schema_version": "1",
  "policy": "strict",
  "layout": { "min_spacing": 0.9, "frame_margin": 0.7, "overlap_policy": "strict" },
  "color": { "approved_palette": ["BLUE", "GOLD", "GREEN", "WHITE", "GREY"] },
  "style": { "stroke_width": 3.0, "fill_opacity": 1.0, "font_size": 32, "animation_run_time": 1.2 }
}
```

### Permissive exploration (no palette restriction)

```json
{
  "schema_version": "1",
  "policy": "warn",
  "color": { "approved_palette": [] },
  "style": { "animation_run_time": 2.0 }
}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `RULES_LOAD_ERROR` | File missing, invalid JSON, or `schema_version != "1"` | Validate JSON syntax; ensure `schema_version` is `"1"` |
| No color diagnostics emitted | `approved_palette` is empty `[]` | Add color names to the palette array |
| `run_time` diagnostics even for small values | `animation_run_time` is very low in config | Increase `style.animation_run_time` or reduce scene `run_time=` kwargs |
