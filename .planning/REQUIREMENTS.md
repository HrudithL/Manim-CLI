# Requirements — ManimAgent v1

Traceability: requirement → phase (see `.planning/ROADMAP.md`).

## v1 Requirements

### Pipeline & control (PIPE)

- [ ] **PIPE-01:** User can run full pipeline from a single natural-language prompt to a final rendered video with iteration transparency (per `instr.md` §3.9, §6).
- [ ] **PIPE-02:** Iteration loop enforces max iterations (default 5), low-quality renders during loop, and final render at user-selected quality.
- [ ] **PIPE-03:** Convergence / stuck detection: repeated CRITICAL/HIGH discrepancy on same object+issue surfaces to user and stops looping.

### API & agent contract (API)

- [ ] **API-01:** Python API exposes pipeline stages with Pydantic-validated inputs/outputs (IR, render result, manifest, critique, fix log).
- [ ] **API-02:** CLI commands can run non-interactively and write deterministic artifact files under a configurable output directory.

### Registry (REG)

- [ ] **REG-01:** `manimagent registry build` parses Manim source with `ast` and emits `registry.json` with class metadata, inheritance, init params, tags, and example pointers per spec.
- [ ] **REG-02:** Registry build can be cached and rebuilt when Manim version changes.

### RAG (RAG)

- [ ] **RAG-01:** Build FAISS index from registry entries for embedding retrieval.
- [ ] **RAG-02:** Retrieval composes a compact context block for prompts and always injects the static Manim coordinate primer (not retrieved).

### Scene IR (IR)

- [ ] **IR-01:** Scene IR matches `instr.md` schema; validated via Pydantic with documented validation rules.
- [ ] **IR-02:** IR validation rejects invalid object ids, out-of-frame positions (unless explicitly noted), invalid animation targets, and timing violations.

### Code generation (CODE)

- [ ] **CODE-01:** IR → Python generates exactly one `Scene` subclass with `construct()`; AST syntax validation with limited LLM retry on failure.
- [ ] **CODE-02:** AST structural validation: Scene subclass, `construct()`, registry warnings for unknown names, security forbids I/O/network/shell in generated code.
- [ ] **CODE-03:** Code IR extraction + diff against intended IR produces pre-render warnings for dropped/changed objects.

### Rendering (REN)

- [ ] **REN-01:** Rendering wrapper runs Manim via subprocess, captures logs, classifies errors (`syntax`, `attribute`, `timeout`, `unknown`), writes `render_result.json`.
- [ ] **REN-02:** On success, extracts keyframes via ffmpeg at IR keyframe times plus first/mid/last baseline frames.

### Manifest (MAN)

- [ ] **MAN-01:** Manifest dumper attaches `_ir_id` to mobjects as specified and dumps per-keyframe spatial state to `manifest.json`.
- [ ] **MAN-02:** Fast/dry-run path avoids full render cost where feasible per spec.

### Critique & fix (CRIT)

- [ ] **CRIT-01:** Visual critic consumes frames + manifest + IR + user intent; outputs only `critique.json` matching schema; verdict + severities.
- [ ] **CRIT-02:** Visual fixer applies RFC 6902 patches to IR and updates code; validates IR and AST after fix; writes `fix_log.json`.

### CLI (CLI)

- [ ] **CLI-01:** Commands: `manimagent render`, `manimagent registry build`, `manimagent inspect`, `manimagent critique` with arguments per `instr.md` §3.9.
- [ ] **CLI-02:** Rich progress display: step, iteration, verdict summary, timings.

### Evaluation (EVAL)

- [ ] **EVAL-01:** Automated tests cover IR validation, AST validator, manifest tagging, and critic/fixer behavior on controlled fixtures.
- [ ] **EVAL-02:** Eval harness implements scenarios E1–E5 and records metrics from `instr.md` §10.

## v2 (deferred)

- Multi-scene workflows, audio, 3D scenes, GUI previewer, cloud backends, user-defined mobject registry entries (see PROJECT.md Out of Scope).

## Traceability

| REQ-ID | Phase |
|--------|-------|
| REN-01, REN-02, MAN-01, MAN-02, CLI-01, CLI-02 | 1 |
| IR-01, IR-02, CODE-01, CODE-02, CODE-03, API-01 | 2 |
| CRIT-01, CRIT-02, PIPE-01, PIPE-02, PIPE-03, API-02 | 3 |
| REG-01, REG-02, RAG-01, RAG-02 | 4 |
| EVAL-01, EVAL-02 | 5 |
