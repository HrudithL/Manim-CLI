# Manim CLI — Skill Router

> **Trigger:** Load this file at the start of any session that involves `manim-cli`. Use the routing table below to load only the sub-skill(s) relevant to your current task. Do not load all files eagerly.

## Task routing

| Current task | Load |
|---|---|
| Scaffolding a new project or adding a scene module | `project-init.md` |
| About to render a scene (any scene) | `pipeline.md` |
| Received `error_code: POLICY_VIOLATION` | `policy-fix.md` |
| Interpreting `analyze scene-file` output or `policy_facts` fields | `scene-analysis.md` |
| Running CI, pre-commit, or batch validation without rendering | `ci-gate.md` |
| Creating, editing, or troubleshooting `rules.json` | `rules-config.md` |
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
