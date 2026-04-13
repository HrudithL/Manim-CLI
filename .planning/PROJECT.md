# ManimAgent (Manim_CLI)

## What This Is

**ManimAgent** is a Python package and CLI that helps LLMs produce reliable Manim Community Edition animations from natural-language user requests. It provides structured capability knowledge (AST-derived registry + retrieval), a geometric **Scene IR** layer, deterministic render/manifest tooling, and a **visual critique → fix** loop so the model can self-correct using frames plus ground-truth mobject state—not guesswork.

Target users: developers and educators orchestrating LLM agents that generate, render, and refine Manim scenes.

## Core Value

**Close the LLM feedback loop:** the system must combine **rendered frames**, **manifest ground truth** (positions, bounds, colors, z-order), and **structured critique** so iterations converge toward the user’s intent without hand-holding.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] **Pipeline:** End-to-end flow from user prompt → IR → validated code → low-Q render → manifest → critic → (optional) fixer iterations → final render; max iterations and stuck detection per spec (`instr.md`).
- [ ] **Library-first API:** Stable Python modules (Pydantic-validated IR, explicit pipeline functions) with predictable errors; CLI is a thin wrapper.
- [ ] **Structured agent I/O:** Each stage can emit machine-readable artifacts (`ir.json`, `scene.py`, `render_result.json`, `manifest.json`, `critique.json`, `fix_log.json`) and CLI supports non-interactive/agent use.
- [ ] **AST Mobject Registry:** Build `registry.json` from Manim source via `ast`; include inheritance, init params, tags, example pointers; cache on Manim version bump.
- [ ] **RAG layer:** FAISS index over registry entries + static Manim coordinate primer always injected; top-K retrieval + re-ranking for IR/code prompts.
- [ ] **Scene IR:** JSON schema (Pydantic), validation rules (frame bounds, animation targets, keyframes at T=0 and T=end, etc.).
- [ ] **IR → Code:** LLM-generated `Scene` subclass with AST validation (syntax + structure), security checks, code-IR extraction, IR diff warnings.
- [ ] **Rendering wrapper:** Subprocess `manim render`, log capture/classification, `render_result.json`, ffmpeg keyframe extraction (+ baseline first/mid/last frames).
- [ ] **Manifest dumper:** Inspectable scene/mixin, `_ir_id` tagging on mobjects, per-keyframe manifest JSON from Manim object graph (dry-run / fast path per spec).
- [ ] **Visual critic:** Vision-capable LLM → `critique.json` only; severity + verdict rules; coordinate-aware discrepancy reporting.
- [ ] **Visual fixer:** RFC 6902 JSON Patch for IR updates + validated code update; CRITICAL/HIGH only; `fix_log.json`.
- [ ] **CLI:** `manimagent render`, `registry build`, `inspect`, `critique` as in `instr.md`; rich progress output.
- [ ] **Eval harness:** Canonical tests E1–E5 and metrics from `instr.md` §10.

### Out of Scope

- **Multi-scene / chapters** — v0.1 is one `Scene` per invocation (`instr.md` §11).
- **Audio / voiceover** — deferred.
- **3D / ThreeDScene** — deferred to v0.2+.
- **GUI / interactive previewer** — CLI only for v0.1.
- **User-defined mobjects in registry** — v0.1 focuses on Manim CE classes.
- **Streaming partial renders** — not in v0.1.
- **Cloud render backends** — local Manim only for v0.1.
- **Prose docs RAG** — registry + structured retrieval replace prose RAG for v0.1.

## Context

- **Specification:** `instr.md` is the authoritative engineering spec (components, schemas, prompts, milestones, tech stack, directory layout).
- **Upstream:** Manim Community Edition (`manim`); system needs `ffmpeg` on PATH; optional LaTeX for `MathTex`.
- **LLM providers:** Spec references Anthropic (`ANTHROPIC_API_KEY`); architecture should keep provider interfaces swappable behind a thin client layer for future models.
- **Embeddings:** Local embedding model (e.g. `sentence-transformers`) for FAISS; no API cost for retrieval index build.
- **Repo layout:** Implement under `manimagent/` package as in `instr.md` §9 (this workspace folder may remain `Manim_CLI` as the working tree name).

## Constraints

- **Tech:** Python 3.11+, `pyproject.toml`, dependencies per `instr.md` §8 (manim, pydantic v2, faiss-cpu, sentence-transformers, anthropic, click, rich, jsonpatch, ffmpeg wrapper, etc.).
- **Quality policy:** Low quality during iteration; final quality user-selected (`instr.md` §6).
- **Security:** Generated code must not perform arbitrary file/network/shell access (AST checks).
- **Performance:** Prefer dry-run manifest + fast renders in the loop; expensive operations only after approval.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Library-first core + CLI wrapper | LLMs need stable, typed, machine-readable contracts; CLI wraps the same code paths. | — Pending |
| Scene IR as canonical intent | Forces spatial planning before Python; critic/fixer target IR deltas. | — Pending |
| Manifest from Manim object graph | Ground truth beats vision-only position estimates. | — Pending |
| Registry from AST + vector retrieval | Reduces hallucinated class/parameter names vs prose-only RAG. | — Pending |

## Deployment & Distribution (open)

- **Local dev:** `uv` or `pip` install from repo; `.env` for API keys.
- **Package name:** Align PyPI/project name with CLI (`manimagent` per spec); confirm branding vs folder name `Manim_CLI`.
- **Optional later:** Docker image with Manim + ffmpeg; CI matrix for Windows/Linux.

---
*Last updated: 2026-04-13 after initialization*
