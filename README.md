# Manim CLI

Standalone **developer** CLI for [Manim Community Edition](https://www.manim.community/) workflows: discover `Scene` subclasses, analyze scene files, validate a Manim-repo-style tree, scaffold a minimal project, and invoke the real `manim` CLI to render.

This package is **not** the Manim library. Install Manim CE separately so `manim` is on your `PATH`.

## Recommended use

- **Audience:** developers and coding agents (structured `--json` output, subprocess-friendly).
- **Install:** treat as its own tool, e.g. with [pipx](https://pipx.pypa.io/) so it stays isolated from app projects:

  ```bash
  pipx install "C:/Users/hrudi/Documents/Personal/Manim_BEI/cli-anything-manim/manim/agent-harness"
  ```

  Or from a clone / sdist / PyPI once published:

  ```bash
  pipx install manim-cli
  ```

- **Manim CE version note:** the CLI is **not** guaranteed to track every Manim CE release. The **last Manim CE version this repo was verified against** is recorded in `manim_cli/manim/_meta.py` as `MANIM_CE_VERIFIED_VERSION` and shown by:

  ```bash
  manim-cli --version
  ```

  Bump that constant when you confirm behavior against a newer Manim CE release.

## Development

```bash
cd "C:/Users/hrudi/Documents/Personal/Manim_BEI/cli-anything-manim/manim/agent-harness"
pip install -e .
manim-cli --help
manim-cli --version
```

## LLM / agent usage

See [LLM_GUIDELINES.md](LLM_GUIDELINES.md) for `--json`, command workflows, and limitations (`validate repo` vs arbitrary projects).
