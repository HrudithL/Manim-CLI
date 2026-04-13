# Roadmap — ManimAgent

Aligned with `instr.md` §7 milestones (M1–M5). Phases are sequential; parallelization in config applies to independent *plans* within a phase, not skipping dependencies.

## Overview

| Phase | Name | Goal | Requirements |
|-------|------|------|----------------|
| 1 | Foundation | Reliable render, frame extraction, manifest dump, CLI skeleton | REN-01, REN-02, MAN-01, MAN-02, CLI-01, CLI-02 |
| 2 | IR layer | Validated Scene IR and codegen with AST gates + IR diff warnings | IR-01, IR-02, CODE-01, CODE-02, CODE-03, API-01 |
| 3 | Critique loop | Critic + fixer + controller; end-to-end iteration with convergence | CRIT-01, CRIT-02, PIPE-01, PIPE-02, PIPE-03, API-02 |
| 4 | Registry & RAG | AST registry builder, FAISS, prompt context injection | REG-01, REG-02, RAG-01, RAG-02 |
| 5 | E2E polish & eval | Full prompt-to-video UX, `--approve-ir`, eval suite | EVAL-01, EVAL-02 (spans all prior REQ for integration) |

## Phase details

### Phase 1 — Foundation

**Goal:** From a hand-written `scene.py`, produce `manifest.json` and keyframe PNGs with Manim-space coordinates verified; establish CLI entrypoints for `render` (subset) and `inspect`.

**Success criteria:**

1. Subprocess render + log capture + `render_result.json` for success and failure cases.
2. ffmpeg extracts frames at requested times plus baseline frames.
3. Manifest records `_ir_id`, centers, bounds, colors, z-index at declared keyframes.
4. `manimagent inspect` runs manifest path without full final-quality render where possible.

### Phase 2 — IR layer

**Goal:** Hand-crafted IR JSON generates valid Manim code, passes AST checks, and manifest matches IR within tolerance.

**Success criteria:**

1. Pydantic IR validates all rules in `instr.md`.
2. Generated code passes syntax + structural AST validation.
3. Code IR extraction flags missing/changed objects vs IR before render.

### Phase 3 — Critique loop

**Goal:** Injected wrong position is detected by critic and fixed within 2 iterations.

**Success criteria:**

1. `critique.json` validates against schema; severities assigned.
2. Fixer applies JSON Patch; IR re-validates; code re-validates.
3. Loop policy matches `instr.md` (max iter, stuck detection).

### Phase 4 — Registry & RAG

**Goal:** For sampled Manim classes, registry entries include params and at least one plausible animation; retrieval returns relevant rows for mock prompts.

**Success criteria:**

1. `registry build` completes on installed Manim.
2. FAISS query returns top-K; primer always appended.
3. IR/code prompts include RAG block in specified XML-ish format.

### Phase 5 — E2E polish & eval

**Goal:** Prompt-to-video for diverse prompts; evaluation harness and metrics.

**Success criteria:**

1. `manimagent render --prompt ...` runs full pipeline.
2. Optional `--approve-ir` pauses for approval.
3. Eval scenarios E1–E5 runnable; metrics recorded.

---
*Generated: 2026-04-13*
