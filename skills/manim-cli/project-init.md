# Skill: Project Initialization

> **Trigger:** When creating a new Manim project or adding a new scene module to an existing project.

## Required project layout

```
project_root/
├── scenes/
│   ├── __init__.py          # empty package marker
│   ├── intro_scene.py       # one Scene subclass per file
│   └── graph_scene.py
├── styles.py                # shared style constants
├── rules.json               # policy config
└── media/                   # render output target
```

## Scaffolding a new project from scratch

### 1. Create the directory structure

```bash
mkdir -p scenes media
touch scenes/__init__.py
```

### 2. Create `rules.json`

```json
{
  "schema_version": "1",
  "policy": "strict",
  "layout": { "min_spacing": 0.9, "frame_margin": 0.7, "overlap_policy": "strict" },
  "color": { "approved_palette": ["BLUE", "GOLD", "GREEN", "WHITE", "GREY"] },
  "style": { "stroke_width": 3.0, "fill_opacity": 1.0, "font_size": 32, "animation_run_time": 1.2 }
}
```

### 3. Create `styles.py`

```python
from manim import BLUE, GOLD, GREEN, WHITE, GREY

STROKE_WIDTH       = 3.0
FONT_SIZE          = 32
ANIMATION_RUN_TIME = 1.2
FILL_OPACITY       = 1.0

PRIMARY   = BLUE
SECONDARY = GOLD
ACCENT    = GREEN
```

Values must match `rules.json` style section. See `rules-config.md` → "Keeping styles.py in sync" for the authoritative field-to-constant mapping.

### 4. Scaffold a scene via CLI

```bash
manim-cli --json --rules-config rules.json project init \
  --target-dir ./tmp_scaffold --scene-name GraphScene
```

> **Warning:** The CLI always writes `<target-dir>/scene.py` — the output filename is fixed and cannot be customized. Do not use `./scenes` as `--target-dir`; if `scenes/scene.py` already exists, the CLI returns `VALIDATION_ERROR`.

**Check:** `ok: true`. Output contains `path` (absolute path to `scene.py`).

### 5. Move and wire up

Move the scaffolded file into the scenes package and replace inline constants:

```bash
mv tmp_scaffold/scene.py scenes/graph_scene.py
rmdir tmp_scaffold
```

Edit `scenes/graph_scene.py`: replace inline `STROKE_WIDTH = ...` definitions with:
```python
from styles import STROKE_WIDTH, FONT_SIZE, ANIMATION_RUN_TIME, FILL_OPACITY
```

### 6. Verify

```bash
manim-cli --json scene list --repo-path ./scenes
```

> **Note:** `scene list` is the one command that does not require `--rules-config`. Omitting it here is intentional and correct — see `README.md` global flags for the general rule.

**Check:** `ok: true`, `scenes[]` contains `GraphScene` with correct `file_path`.

## Adding a scene to an existing project

Each new scene goes in its own `scenes/<topic>_scene.py` file. Follow these commands:

```bash
# 1. Scaffold into a temp dir (never scaffold directly into scenes/)
manim-cli --json --rules-config rules.json project init \
  --target-dir ./tmp_scaffold --scene-name MyNewScene

# 2. Move into the scenes package
mv tmp_scaffold/scene.py scenes/my_new_scene.py
rmdir tmp_scaffold
```

Edit `scenes/my_new_scene.py`: replace inline constant definitions with the shared import:
```python
from styles import STROKE_WIDTH, FONT_SIZE, ANIMATION_RUN_TIME, FILL_OPACITY
```

```bash
# 3. Verify the scene is discoverable
manim-cli --json scene list --repo-path ./scenes
```

**Check:** `ok: true`, `scenes[]` contains `MyNewScene` with correct `file_path`.

## Naming conventions

| Item | Convention | Example |
|---|---|---|
| Module file | `snake_case` | `graph_scene.py` |
| Class name | `PascalCase` matching topic | `GraphScene` |
| Style constants | `UPPER_SNAKE_CASE` in `styles.py` only | `STROKE_WIDTH` |

## Constraints

- `project init` always writes `<target-dir>/scene.py` — it cannot write to a custom filename.
- Returns `error_code: VALIDATION_ERROR` if `scene.py` already exists in `--target-dir`.
- Never place more than one Scene subclass per file.
- Never define magic style values inline in scene files — import from `styles.py`.

## See Also

| Skill | Purpose |
|---|---|
| `rules-config.md` | `rules.json` schema and `styles.py` sync table |
| `pipeline.md` | Mandatory render pipeline to run after scaffolding |
| `scene-analysis.md` | Pre-validation checklist for newly scaffolded scenes |
