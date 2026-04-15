# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode (required before running CLI)
pip install -e .

# Run all tests
python -m pytest tests/ -q

# Run a single test file
python -m pytest tests/test_render.py -q

# Run a single test by name
python -m pytest tests/test_render.py::test_build_render_command_contains_expected_parts -q

# Run the CLI directly (without installing)
python -m manim_cli.manim.cli --help
```

## Architecture

The CLI is built with [Click](https://click.palletsprojects.com/) and lives entirely under `manim_cli/manim/`. The entry point is `manim_cli/manim/cli.py` (`manim-cli` console script).

### Request flow

Every command follows the same pattern in `cli.py`:
1. `main` group loads `GlobalRules` from `--rules-config` (or defaults) and stores it in `ctx.obj`
2. The subcommand calls the relevant core function from `core/`
3. The result dict is wrapped in a JSON envelope via `utils/output.py` and emitted

### Core modules (`manim_cli/manim/core/`)

| Module | Responsibility |
|---|---|
| `constants.py` | `MANIM_COLOR_NAMES` frozenset + `MANIM_SCENE_BASE_NAMES` frozenset — single source of truth, bump both when updating `MANIM_CE_VERIFIED_VERSION` |
| `rules.py` | `GlobalRules` dataclass (layout/color/style/policy), `load_rules()`, `default_rules()` |
| `scene_index.py` | AST-based `discover_scenes()` — per-file inheritance graph + BFS against `MANIM_SCENE_BASE_NAMES`; catches all first-party Manim scene types and user-defined intermediate bases in the same file |
| `analyze.py` | `analyze_scene_file()` — deeper AST pass: play calls, mobject calls, `policy_facts` |
| `render.py` | `run_render()` + `_run_policy_checks()` + `_run_layout_checks()` — the pre-render gate |
| `validate.py` | `validate_repo()`, `validate_scene_style()`, `validate_scene_layout()` — wraps `render._run_policy_checks` |
| `watch.py` | `watch_scene_file()` — polling generator; yields a validation result dict on every file change |
| `fix.py` | `apply_fixes()` — patches source lines from diagnostics; auto-fixes `color.out_of_palette` and `style.animation_run_time`; layout rules are left as unfixed |
| `project.py` | `init_project()` — scaffolds `scene.py` from a rules-aware template |
| `install.py` | `install_skills()` — copies bundled skill `.md` files into agent-specific directories |

### JSON envelope contract

`utils/output.py` defines the stable output shape. Every `--json` response has:
- `ok`, `schema_version`, `command`, `timestamp` — always present
- `error`, `error_code` — present on failure

Error codes are defined in `output.py::ERROR_CODES`. Never introduce a new error code without adding it to that set.

### `watch scene-file`

`watch scene-file --scene-file PATH [--poll-interval N]` blocks and re-runs `_run_policy_checks` every time the file's mtime changes. The first result is emitted immediately. Output is one JSON envelope per change (consistent with every other `--json` command). Ctrl-C exits cleanly. The "Watching…" / "Stopped." banners go to stderr so they never pollute `--json` output.

### `fix apply`

`fix apply --scene-file PATH [--dry-run]` runs `_run_policy_checks`, groups diagnostics by line number, and patches lines in-place. Two rules are auto-fixable:
- **`color.out_of_palette`** — extracts the color name from the diagnostic message and swaps it for the alphabetically-first approved palette color using word-boundary regex.
- **`style.animation_run_time`** — extracts the max threshold from the `fix_hint` and replaces `run_time=<N>` on the line.

Layout diagnostics (`layout.*`) are never auto-patched — they appear in `unfixed_diagnostics` with their `fix_hint` intact. `--dry-run` computes fixes without writing. When `fix-ready` policy is active, chain `fix apply` before `render run` to clear warnings before the render gate.

### Policy / rules system

`GlobalRules` has three sub-schemas (`LayoutRules`, `ColorRules`, `StyleRules`) and a `policy` mode (`warn` | `strict` | `fix-ready`). Rules flow through `ctx.obj["rules"]` into every command. The pre-render gate in `render._run_policy_checks()` and `render._run_layout_checks()` produces `diagnostics` dicts with `rule_id`, `severity`, `message`, `location`, and optional `fix_hint`. All layout rule IDs are prefixed `layout.`; color rules are prefixed `color.`; style rules are prefixed `style.`.

### Skills system

`manim_cli/skills/manim-cli/` contains bundled Markdown skill files that agents (Claude, Copilot, generic) load for task routing. `install_skills()` copies them to `.claude/skills/manim-cli/`, `.github/skills/manim-cli/`, or `skills/manim-cli/` depending on the `--agent` flag. `SKILL.md` is the router that specifies which sub-skills to load for which task type.

### Repo layout expected by `validate_repo`

`validate repo` expects a `manim/` subdirectory at the top level of the target repo (repo-first layout). If it is missing, the command returns `VALIDATION_ERROR`. Beyond that gate, it runs three additional checks whose results appear in the `checks` dict:
- **`requirements_file`** — presence of `requirements.txt` or `pyproject.toml` (warning if absent, never blocks `ok`)
- **`manim_pinned`** — whether `manim` appears in that requirements file (warning if missing)
- **`syntax_errors`** — `ast.parse` sweep of all `.py` files; a syntax error IS an error and sets `ok=False`

The return dict always has `errors` (blocking), `warnings` (non-blocking), `checks` (structured per-check results), and `scene_count`.
