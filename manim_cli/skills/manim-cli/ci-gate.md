# Skill: CI / Pre-commit Gate

> **Trigger:** When running policy-only validation without rendering — CI pipelines, pre-commit hooks, or batch file checks.

## Single-file strict gate

```bash
manim-cli --json --rules-config rules.json validate scene-style --scene-file <file_path>
```

**Pass criteria (strict mode):**
- `ok: true`
- `error_count: 0`
- `warning_count: 0`

**Fail:** `ok: false` with `error_code: POLICY_VIOLATION`. Read `diagnostics[]` for details.

## Batch validation — all scenes in a project

Combine `scene list` with per-file validation:

```bash
# Step 1: discover all scene files
manim-cli --json scene list --repo-path ./scenes

# Step 2: for each file_path in scenes[]:
manim-cli --json --rules-config rules.json validate scene-style --scene-file <file_path>
```

An agent should iterate over every `file_path` from step 1 and validate each one. The pipeline passes only when all files return `ok: true`.

## Exit code usage

When `--json` is active, always parse the JSON `ok` field rather than relying on process exit codes. The CLI sets non-zero exit for failures, but the JSON `ok` + `error_code` fields are the authoritative contract.

## CI script pattern

```bash
#!/bin/bash
set -e

# Validate all scene files under strict policy
FILES=$(manim-cli --json scene list --repo-path ./scenes | python -c "
import sys, json
data = json.load(sys.stdin)
for s in data.get('scenes', []):
    print(s['file_path'])
")

FAILED=0
for f in $FILES; do
  RESULT=$(manim-cli --json --rules-config rules.json validate scene-style --scene-file "$f")
  OK=$(echo "$RESULT" | python -c "import sys,json; print(json.load(sys.stdin)['ok'])")
  if [ "$OK" != "True" ]; then
    echo "FAIL: $f"
    echo "$RESULT"
    FAILED=1
  fi
done

exit $FAILED
```

## What the gate checks

Only two rules are enforced by the CLI:

| `rule_id` | Condition |
|---|---|
| `color.out_of_palette` | Color constant not in `approved_palette` (only when palette is non-empty) |
| `style.animation_run_time` | `run_time=` kwarg exceeds 3x `style.animation_run_time` |

Everything else (overlap, label density, stroke width, font size) must be enforced at the authoring level or via a separate linter.

## Pre-commit hook integration

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: manim-style-gate
      name: Manim scene style validation
      entry: bash -c 'for f in "$@"; do manim-cli --json --rules-config rules.json validate scene-style --scene-file "$f" || exit 1; done' --
      language: system
      files: 'scenes/.*\.py$'
      types: [python]
```
