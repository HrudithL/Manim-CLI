# Skill: Layout Validator Gate

> **Trigger:** Any request that requires no visual overlaps, no clipped axes, or no objects covering each other.

## Goal

Fail fast when layout risks are detected so bad scenes never pass CI or render in strict pipelines.

## Mandatory command

```bash
manim-cli --json --rules-config rules.json validate scene-layout --scene-file <file_path>
```

## Pass/fail contract

- **Pass:** `ok: true`, `error_count: 0`, `warning_count: 0` (strict policy).
- **Fail:** `ok: false` with `error_code: POLICY_VIOLATION`.

Treat all `layout.*` diagnostics as blocking in strict mode.

## Layout rule IDs

| `rule_id` | Meaning | Typical fix |
|---|---|---|
| `layout.unpositioned_add` | Object added without explicit positioning | Add `.next_to()`, `.move_to()`, `.to_edge()`, or `.to_corner()` before `self.add(...)` |
| `layout.label_overlap_risk` | Multiple labels appear unpositioned | Position each label explicitly and tune `buff` |
| `layout.graph_label_not_anchored` | Label not anchored to graph/axes | Use `label.next_to(axes_or_graph, buff=<n>)` |
| `layout.axis_frame_margin` | Axis edge buffer below required frame margin | Increase `to_edge(..., buff=...)` to at least `layout.frame_margin` |

## Required pipeline placement

Insert this after style validation and before dry-run:

1. `scene list`
2. `analyze scene-file`
3. `validate scene-style`
4. `validate scene-layout`  ← required
5. `render run --dry-run`
6. `render run`

## Rules config knobs

Configure in `rules.json`:

```json
"layout": {
  "min_spacing": 0.9,
  "frame_margin": 0.7,
  "overlap_policy": "strict",
  "max_bbox_intersection_ratio": 0.0,
  "axis_label_padding": 0.2,
  "sample_frames_per_animation": 8
}
```

## CI requirement

CI must run both:

- `validate scene-style`
- `validate scene-layout`

and fail if either returns `ok: false`.
