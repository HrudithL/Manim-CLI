# LLM instructions: using `Manim CLI`

This document tells coding agents and LLM-driven workflows how to use the **manim-cli** harness safely and effectively. Point your system prompt, project rules, or skill loader at this file (or paste a short summary into the agent context).

## What this tool is

- A **standalone developer-focused** **Click** CLI around **Manim Community Edition** workflows: discover `Scene` subclasses, analyze Python scene files, validate a repo layout, scaffold a minimal project, and **invoke the real `manim` executable** to render.
- Output is **human text** by default; for agents, always pass **`--json`** (alias: `--json-output`) so responses are **single-document JSON** on stdout.
- **Manim CE alignment:** the harness does not pin Manim. The maintainers record the **last Manim CE version verified** in `manim_cli/manim/_meta.py` (`MANIM_CE_VERIFIED_VERSION`); `manim-cli --version` prints that value for reference only — it is **not** a strict compatibility guarantee.

## Workspace root assumption

Assume all relative paths are based from:

`C:/Users/hrudi/Documents/Personal/Manim_BEI/cli-anything-manim/manim/agent-harness`

## Prerequisites (check before promising results)

1. **Install the harness** (from `manim/agent-harness`):

   ```bash
   pip install -e .
   ```

2. **Real renders** require the **`manim`** CLI on `PATH` (Manim CE installed in the same environment). If `manim` is missing, `render run` returns JSON with `ok: false` and an error about the executable.

3. **`validate repo`** expects a **clone of [ManimCommunity/manim](https://github.com/ManimCommunity/manim)**-style layout: a top-level directory named **`manim/`** (the library package). Arbitrary user projects may fail validation even if they are valid Manim projects—use `scene list` / `analyze` for those.

## Golden rules for LLMs

1. **Prefer `--json` on every invocation** so you can parse output without guessing table formatting.
2. **Use absolute paths** when the user’s OS mixes drives or spaces (Windows: quote paths in shell snippets).
3. **Discover before you render**: list scenes (`scene list`) or read analysis (`analyze scene-file`) so `scene-name` matches an actual class name.
4. **Use `render run --dry-run` first** to confirm the exact `manim` command line (quality, renderer, media dir) before spending time on a full render.
5. **Do not fabricate paths**: `scene-file` and `--repo-path` must exist; the CLI validates existence where noted below.
6. **Treat stderr separately**: subprocess wrappers should capture stdout (JSON) and stderr (Click errors, environment issues) distinctly.

## Command reference (agent-oriented)

Global:

| Flag | Meaning |
|------|---------|
| `--json` / `--json-output` | Emit structured JSON for the subcommand (recommended). |
| `-h` / `--help` | Standard help. |

### `project init`

Create a minimal `scene.py` with a `Scene` subclass.

```text
manim-cli --json project init --target-dir <DIR> [--scene-name HelloScene]
```

- **When to use**: bootstrap a new folder for generated or hand-edited scenes.

### `scene list`

Scan a directory tree for classes that inherit from `Scene` (heuristic: bases named `Scene` or `*.Scene`).

```text
manim-cli --json scene list --repo-path <EXISTING_DIR>
```

- **Returns**: `ok`, `count`, `scenes[]` with `name`, `file_path`, `lineno`.
- **When to use**: find which scene class to pass to `render run`.

### `render run`

Invoke **real** Manim: `manim -q<quality> --renderer=<renderer> [--media_dir <dir>] <scene-file> <scene-name>`.

```text
manim-cli --json render run \
  --scene-file <EXISTING_PY> \
  --scene-name <ClassName> \
  [--quality l] \
  [--renderer cairo] \
  [--output-dir <MEDIA_DIR>] \
  [--dry-run]
```

- **`--quality`**: single letter passed as `-q<quality>` (default `l` = low).
- **`--renderer`**: passed as `--renderer=...` (default `cairo`).
- **`--output-dir`**: maps to Manim’s `--media_dir`.
- **`--dry-run`**: does not call `manim`; response includes the resolved `command` array and `ok: true` if the CLI would run.

**Success JSON (non-dry)** includes `returncode`, `stdout`, `stderr`, and optional `output_root`. **`ok`** is true when `returncode == 0`.

### `analyze scene-file`

Lightweight **AST** summary: classes, `play(...)` call sites, and calls that look like mobject constructors (capitalized names).

```text
manim-cli --json analyze scene-file --scene-file <EXISTING_PY>
```

- **When to use**: quick structural read of a file before editing or rendering.

### `validate repo`

Checks that the path exists, that **`manim/`** exists under it (upstream repo layout), and that at least one `Scene` subclass was discovered.

```text
manim-cli --json validate repo --repo-path <DIR>
```

- **When to use**: sanity-check a **cloned Manim CE repository**. Not a substitute for validating arbitrary user animation repos.

## REPL mode

Running **`manim-cli`** with **no subcommand** starts an interactive REPL (`manim>`). It is intended for humans; **agents should prefer one-shot shell commands** with `--json` instead of driving the REPL unless the host environment cannot spawn subprocesses.

## Suggested agent workflows

### A. Work inside a cloned Manim CE repo

1. `validate repo --repo-path <clone>` → confirm layout + non-zero scene count.
2. `scene list --repo-path <clone>` → pick `name` and `file_path`.
3. `analyze scene-file --scene-file <file>` → optional structural check.
4. `render run ... --dry-run` → verify command.
5. `render run ...` (no dry-run) → produce media; read `stdout`/`stderr` from JSON if `ok` is false.

### B. Work in a user project (only `scene.py` / arbitrary tree)

1. Skip `validate repo` if there is no top-level `manim/` package folder.
2. `scene list --repo-path <project_root>` → discover scenes.
3. Continue with `analyze` and `render` as above.

### C. Scaffold then render

1. `project init --target-dir <new_dir> --scene-name MyScene`
2. Edit `scene.py` as needed (or let the user edit).
3. `render run --scene-file <new_dir>/scene.py --scene-name MyScene --dry-run` then render.

## Error handling for agents

- Parse **stdout** as JSON when `--json` is set.
- If the process exits non-zero or stdout is not JSON, surface **stderr** to the user (missing `manim`, bad paths, Click usage errors).
- For `render run`, a failed render still returns JSON with `ok: false`; inspect `stderr` for LaTeX, FFmpeg, or Manim tracebacks.

## Security and safety notes

- This CLI runs **`manim` as a subprocess** with user-supplied file paths and scene names. Only point it at paths the user trusts.
- **Dry-run** does not execute Manim; use it when exploring untrusted trees.

## Minimal copy-paste block for system prompts

```text
You have access to manim-cli. Always call it with --json.
Discover scenes: manim-cli --json scene list --repo-path <DIR>
Render (check first): manim-cli --json render run --scene-file <FILE.py> --scene-name <Class> --dry-run
Render: same without --dry-run; requires manim on PATH.
Validate upstream clone only: manim-cli --json validate repo --repo-path <DIR>
Analyze file: manim-cli --json analyze scene-file --scene-file <FILE.py>
```

---

*Harness layout: `manim/agent-harness/`. Entry point: `manim-cli`.*
