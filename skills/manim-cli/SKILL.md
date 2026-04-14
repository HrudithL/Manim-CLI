# Manim CLI — Skill Router

> **Trigger:** Load this file at the start of any session that involves `manim-cli`.
>
> **Hard requirement for build/develop work:** For any request to build, develop, implement, fix, or refactor Manim scenes, load **all** sub-skills before taking the first CLI action.

## Mandatory preload for build/develop tasks

For build/develop tasks, this exact checklist is required:

1. Load `README.md`
2. Load `project-init.md`
3. Load `pipeline.md`
4. Load `policy-fix.md`
5. Load `scene-analysis.md`
6. Load `ci-gate.md`
7. Load `rules-config.md`
8. Load `validator.md`

Before invoking `manim-cli`, emit a `skills_loaded` record showing all eight entries as loaded.

## Task routing (non-build tasks)

| Current task | Load |
|---|---|
| Scaffolding a new project or adding a scene module | `project-init.md` |
| About to render a scene (any scene) | `pipeline.md` |
| Received `error_code: POLICY_VIOLATION` | `policy-fix.md` |
| Interpreting `analyze scene-file` output or `policy_facts` fields | `scene-analysis.md` |
| Running CI, pre-commit, or batch validation without rendering | `ci-gate.md` |
| Creating, editing, or troubleshooting `rules.json` | `rules-config.md` |
| Enforcing zero-overlap/zero-clipping layout constraints | `validator.md` |
| General orientation, error code lookup, or global flags | `README.md` |

## Quick decision tree

```
Need to render a scene?
  └─ Yes → load pipeline.md
       └─ Got POLICY_VIOLATION? → also load policy-fix.md
       └─ Step 2 fields confusing? → also load scene-analysis.md

Setting up a new project?
  └─ Yes → load project-init.md
       └─ Need to configure rules.json? → also load rules-config.md

Running CI or pre-commit only?
  └─ Yes → load ci-gate.md
```

## Sub-skills index

| File | Trigger |
|---|---|
| `README.md` | Global flags, JSON envelope contract, error code table |
| `pipeline.md` | Mandatory 5-step render pipeline (always use this for rendering) |
| `project-init.md` | New project scaffold or adding a scene module |
| `policy-fix.md` | Fix loop after `POLICY_VIOLATION` |
| `scene-analysis.md` | `policy_facts` field reference and pre-validation checklist |
| `ci-gate.md` | Bash and PowerShell CI scripts, pre-commit hook integration |
| `rules-config.md` | `rules.json` schema, policy modes, `styles.py` sync table |
| `validator.md` | Mandatory layout validator gate for overlap and clipping risks |
