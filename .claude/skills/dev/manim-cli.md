# Manim CLI — Developer Skill

> **Trigger:** When contributing to the manim-cli codebase itself — adding commands, fixing bugs, modifying the JSON contract, or running tests.

## Project structure

```
manim_cli/
├── manim/
│   ├── cli.py           # Click CLI entry point — all commands registered here
│   ├── _meta.py         # MANIM_CE_VERIFIED_VERSION constant
│   ├── core/
│   │   ├── analyze.py   # AST analysis of scene files → policy_facts
│   │   ├── install.py   # install --skills logic (copies bundled skill files)
│   │   ├── project.py   # project init scaffolding
│   │   ├── render.py    # subprocess wrapper for real manim renders
│   │   ├── rules.py     # GlobalRules dataclass, load_rules(), default_rules()
│   │   ├── scene_index.py  # scene list discovery via rglob
│   │   └── validate.py  # validate repo + validate scene-style (policy checks)
│   └── utils/
│       └── output.py    # build_envelope(), build_error_envelope(), emit()
├── skills/
│   ├── __init__.py      # package marker for importlib.resources
│   └── manim-cli/       # bundled agent skill markdown files (7 files)
skills/                  # repo-root reference copy of skill files
tests/                   # pytest test suite
```

Entry point: `manim_cli.manim.cli:main` (registered as `manim-cli` console script).

## Running tests

```bash
python -m pytest tests/ -v
```

Individual test files:
- `test_analyze_validate.py` — analyze + validate scene-style integration
- `test_cli_subprocess.py` — end-to-end CLI invocation via subprocess
- `test_render.py` / `test_render_e2e.py` — render command (mocked + real)
- `test_rules.py` — rules loading, validation, defaults
- `test_scene_index.py` — scene discovery

## JSON envelope contract

Every `--json` response must include these top-level fields:

| Field | Type | Required |
|---|---|---|
| `ok` | bool | always |
| `schema_version` | `"1"` | always |
| `command` | string | always |
| `timestamp` | UTC ISO-8601 | always |
| `error` | string | on failure |
| `error_code` | string | on failure |

Use `build_envelope()` and `build_error_envelope()` from `utils/output.py`. Never construct envelope dicts manually.

## Adding a new CLI command

1. Create the core logic in `manim_cli/manim/core/<module>.py` — return a dict with at minimum `ok: bool`.
2. Import the function in `cli.py`.
3. Add the Click command or subcommand, following the existing pattern:
   - Retrieve `json_output` via `_json_mode(ctx)` and `rules` via `_get_rules(ctx)`.
   - Wrap the core call in try/except, delegating to `_handle_exception()`.
   - Use `build_envelope()` for success and let `_handle_exception()` handle errors.
4. Add tests in `tests/`.
5. If the command introduces a new `error_code`, add it to `ERROR_CODES` in `utils/output.py`.

## Adding a new error code

1. Add the code string to `ERROR_CODES` set in `manim_cli/manim/utils/output.py`.
2. Add a row to the error code table in `LLM_GUIDELINES.md`.
3. Add handling in `_handle_exception()` in `cli.py` if the exception type is new.

## Modifying skill files

Skill files live in two places that must stay in sync:
- `skills/manim-cli/` — repo-root reference copy (edit here)
- `manim_cli/skills/manim-cli/` — package copy (deployed via `pip install`)

After editing the repo-root copy, sync to the package:
```bash
cp skills/manim-cli/*.md manim_cli/skills/manim-cli/
```

## Policy checks

Only two rules are enforced in `validate.py` `_run_policy_checks()`:
- `color.out_of_palette` — fires when a Manim color constant is not in `approved_palette`
- `style.animation_run_time` — fires when `run_time=` kwarg exceeds 3x the configured threshold

Adding a new policy check:
1. Add detection logic to `_run_policy_checks()` in `validate.py`.
2. Return a diagnostic dict with `rule_id`, `severity`, `message`, `location`, and `fix_hint`.
3. Update `LLM_GUIDELINES.md` to document the new rule.
4. Update the `policy-fix.md` and `scene-analysis.md` skill files.
