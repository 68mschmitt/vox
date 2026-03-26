# Implementation Phases

## Overview

The implementation is broken into 3 phases: POC, Alpha, and MVP. Each phase produces a usable artifact. The system is designed so that each phase builds on the previous one without requiring rewrites.

**Total estimated implementation time: 4-6 weeks for a single developer.**

---

## Phase 1: POC (Proof of Concept)

**Goal:** Validate that the core loop works -- generate a persona from seed input, run one calibration round, and produce a usable system prompt.

**Timeline:** 1-1.5 weeks

**Success criteria:** A human can run the tool, create a persona, calibrate it through 1 round, and export a system prompt that noticeably captures their voice when used in Claude Code.

### What to Build

```
persona_forge/
├── main.py              # CLI entry: new, calibrate (1 round), export
├── config.py            # Constants only
├── llm/
│   ├── __init__.py
│   ├── provider.py      # LLMProvider protocol
│   └── anthropic.py     # Single provider (Claude)
├── seed/
│   ├── __init__.py
│   ├── interview.py     # Structured interview (8 questions, hardcoded)
│   └── generator.py     # generate_persona_from_seed
├── calibrate/
│   ├── __init__.py
│   ├── loop.py          # Single-round calibration only
│   ├── questions.py     # Broad coverage question generation (no adaptive)
│   └── evaluator.py     # 4-dimension scoring + divergence report
├── export/
│   ├── __init__.py
│   └── renderer.py      # Full export format only
├── persona/
│   ├── __init__.py
│   ├── model.py         # Persona dataclass (core traits only)
│   └── store.py         # Save/load JSON (no versioning)
├── prompts/
│   ├── __init__.py
│   └── templates.py     # Seed + calibration + evaluation + export prompts
└── ui/
    ├── __init__.py
    └── display.py       # Basic print formatting
```

### POC Scope Details

| Component          | POC Scope                                    | Deferred to Later |
|--------------------|----------------------------------------------|-------------------|
| LLM Provider       | Anthropic only                               | OpenAI, Ollama    |
| Seed Interview     | 8 hardcoded questions + 2 generated Q&A      | Customizable questions |
| Persona Schema     | 8 core traits + values + frustrations        | decision_heuristics, tech_preferences, anti_patterns |
| Calibration        | 1 round, 6 questions, broad coverage only    | Multi-round, adaptive, overhaul |
| Evaluation         | LLM scoring only (no human quick-rating)     | Human ratings, blind test, consistency check |
| Mutation           | Display divergence report, manual persona edit | Auto-propose, approve/reject flow |
| Export             | Full format only, print to stdout            | Compact, one-liner, file output, validation |
| Storage            | Single JSON file, no versioning              | Versions, sessions, tags, golden exemplars |
| CLI                | `new`, `calibrate`, `export`                 | All other commands |

### POC Implementation Order

```
Day 1-2: Foundation
  ├── config.py (constants)
  ├── llm/provider.py (Protocol definition)
  ├── llm/anthropic.py (API wrapper)
  ├── persona/model.py (Persona dataclass)
  └── persona/store.py (save/load single JSON)

Day 3-4: Seed Phase
  ├── prompts/templates.py (seed prompts)
  ├── seed/interview.py (structured interview flow)
  ├── seed/generator.py (call LLM, parse response)
  └── main.py (wire up `new` command)

Day 5-6: Calibration Phase
  ├── prompts/templates.py (calibration + evaluation prompts)
  ├── calibrate/questions.py (broad coverage generation)
  ├── calibrate/evaluator.py (4-dimension scoring)
  ├── calibrate/loop.py (single round orchestration)
  └── main.py (wire up `calibrate` command)

Day 7: Export Phase
  ├── export/renderer.py (full format template)
  ├── main.py (wire up `export` command)
  └── End-to-end test: new → calibrate → export → use in Claude Code
```

### POC Validation

Run the full flow end-to-end:
1. `persona-forge new` -- create a persona from seed input
2. `persona-forge calibrate <id>` -- run 1 calibration round
3. `persona-forge export <id>` -- render as system prompt
4. Paste into Claude Code's CLAUDE.md, ask 5 questions, evaluate subjectively

**POC is successful if:** The exported persona produces answers that are noticeably different from a generic Claude response and roughly match the human's style.

---

## Phase 2: Alpha

**Goal:** Full calibration loop with multi-round support, versioning, human interaction model, and trait mutation. The system can produce genuinely well-calibrated personas.

**Timeline:** 1.5-2 weeks (builds on POC)

**Success criteria:** A human can run 3-4 calibration rounds, see measurable score improvement, and export a persona that consistently matches their voice across diverse questions.

### What to Build (additions to POC)

```
Changes:
  ├── config.py            # + calibration parameters, thresholds
  ├── llm/
  │   └── ollama.py        # + Ollama provider for local dev
  ├── calibrate/
  │   ├── loop.py          # REWRITE: multi-round, convergence, stall detection
  │   ├── questions.py     # + adaptive focus, adversarial questions
  │   ├── evaluator.py     # + human quick-rating, score reconciliation
  │   └── mutator.py       # NEW: trait change proposals, oscillation detection
  ├── persona/
  │   ├── model.py         # + decision_heuristics, tech_preferences, anti_patterns
  │   └── store.py         # REWRITE: versioned storage, sessions, golden exemplars
  ├── prompts/
  │   └── templates.py     # + mutator prompt, overhaul prompt
  └── ui/
      └── display.py       # + progress bars, side-by-side, change proposals
```

### Alpha Scope Details

| Component          | Alpha Scope                                             | Deferred to MVP |
|--------------------|---------------------------------------------------------|-----------------|
| LLM Provider       | + Ollama                                                | OpenAI          |
| Calibration        | Multi-round (up to 4), adaptive questions, convergence  | Overhaul escape hatch |
| Evaluation         | + Human quick-ratings, score reconciliation             | Blind test, consistency check |
| Mutation           | Auto-propose, human approve/reject/modify               | Context-dependent trait splitting |
| Storage            | Full versioning, sessions, trait change log              | Version tagging |
| Golden Exemplars   | Auto-select from high-scoring Q&A pairs                 | Manual curation |
| CLI                | + `show`, `diff`, `revert`                              | `test`, `tag`, `validate`, `list` |
| Export             | + Compact format                                        | One-liner, validation, model tiers |

### Alpha Implementation Order

```
Week 1: Calibration Loop Core
  Day 1: persona/store.py rewrite (versioning, sessions)
  Day 2: persona/model.py expansion (new fields) + prompts update
  Day 3: calibrate/mutator.py (trait proposals, oscillation detection)
  Day 4: calibrate/loop.py rewrite (multi-round, convergence)
  Day 5: calibrate/evaluator.py (human quick-rating, reconciliation)

Week 2: Polish and Utility
  Day 1: calibrate/questions.py (adaptive focus, adversarial)
  Day 2: ui/display.py (progress, side-by-side, proposals)
  Day 3: export/renderer.py (compact format)
  Day 4: CLI commands (show, diff, revert)
  Day 5: End-to-end testing with real calibration sessions
```

### Alpha Validation

Full calibration session:
1. `persona-forge new` -- create persona
2. `persona-forge calibrate <id>` -- run 3-4 rounds
3. Verify scores improve across rounds
4. `persona-forge diff <id> 1 <latest>` -- confirm meaningful trait evolution
5. `persona-forge export <id>` -- export and use in Claude Code
6. Ask 10 diverse questions, compare persona answers to personal answers

**Alpha is successful if:** Scores measurably improve across calibration rounds (from ~6 to ~8), and the exported persona produces answers that a colleague could mistake for the human's.

---

## Phase 3: MVP (Minimum Viable Product)

**Goal:** Production-ready tool with full evaluation suite, multi-provider support, export validation, and all CLI commands. Ready for other people to use.

**Timeline:** 1.5-2 weeks (builds on Alpha)

**Success criteria:** Another person (not the developer) can install the tool, create and calibrate a persona without documentation beyond `--help`, and deploy it successfully.

### What to Build (additions to Alpha)

```
Changes:
  ├── llm/
  │   └── openai.py        # + OpenAI provider
  ├── calibrate/
  │   ├── loop.py          # + overhaul escape hatch
  │   ├── evaluator.py     # + blind comparison, consistency check, regression testing
  │   └── mutator.py       # + context-dependent trait splitting
  ├── export/
  │   └── renderer.py      # + one-liner, model tiers, validation pipeline
  ├── persona/
  │   └── store.py         # + version tagging
  └── ui/
      └── display.py       # + export validation report display

New files:
  ├── validate.py          # Cross-model validation pipeline
  └── tests/
      ├── test_prompts.py  # Prompt output format compliance
      ├── test_scoring.py  # Score distribution tests
      ├── test_store.py    # Versioning and persistence tests
      └── test_e2e.py      # End-to-end flow tests
```

### MVP Scope Details

| Component            | MVP Scope                                              |
|----------------------|--------------------------------------------------------|
| LLM Provider         | Anthropic, OpenAI, Ollama (all three)                  |
| Calibration          | Full loop with overhaul escape hatch                   |
| Evaluation           | Full suite: blind test, consistency, regression        |
| Mutation             | Full: proposals, oscillation prevention, trait splitting|
| Storage              | Full: versioning, sessions, tags, golden exemplars     |
| Export               | All 3 formats, model tier awareness, validation        |
| CLI                  | All commands: new, calibrate, export, validate, show, diff, revert, tag, list, test |
| Testing              | Prompt compliance, scoring, storage, e2e               |

### MVP Implementation Order

```
Week 1: Advanced Evaluation + Multi-Provider
  Day 1: llm/openai.py + provider selection logic
  Day 2: calibrate/evaluator.py (blind comparison, consistency check)
  Day 3: calibrate/evaluator.py (regression testing)
  Day 4: calibrate/loop.py (overhaul escape hatch)
  Day 5: calibrate/mutator.py (context-dependent trait splitting)

Week 2: Export Validation + Testing + Polish
  Day 1: export/renderer.py (one-liner, model tiers)
  Day 2: validate.py (cross-model validation pipeline)
  Day 3: CLI commands (test, tag, validate, list)
  Day 4: tests/ (all test files)
  Day 5: End-to-end testing, edge cases, error handling
```

### MVP Validation

1. **Developer test:** Full flow with all 3 providers
2. **User test:** Hand the tool to someone else, observe them create and calibrate a persona without help
3. **Cross-model test:** Calibrate with Claude, validate against GPT-4, verify scores hold
4. **Regression test:** Run test suite, verify all prompts produce compliant output
5. **Durability test:** Calibrate 3 different personas, verify storage handles multiple personas correctly

**MVP is successful if:** A non-developer can create a calibrated persona in under an hour, export it, and use it successfully in their preferred AI coding tool.

---

## Post-MVP Considerations

Things explicitly out of scope for MVP but worth considering later:

| Feature                     | Rationale for Deferral                                    |
|-----------------------------|----------------------------------------------------------|
| Web UI                      | CLI is sufficient for target users; web UI adds massive complexity |
| Database storage             | JSON files are sufficient for <100 personas               |
| Embedding-based evaluation   | LLM-as-judge is good enough; embeddings add a dependency  |
| Auto-calibration (no human)  | Human-in-the-loop is the core value prop; removing it changes the product |
| Persona marketplace/sharing  | Requires auth, hosting, trust model -- different product   |
| Fine-tuning integration      | Prompt-based approach works well enough; fine-tuning is a 10x complexity increase |
| Team personas                | Start with individual personas; team dynamics are harder   |

## Dependency Map

```
Phase 1 (POC):
  main.py ──► seed/ ──► llm/ ──► prompts/
           ──► calibrate/ ──► llm/ ──► prompts/
           ──► export/ ──► persona/
  
  All phases depend on: persona/model.py, persona/store.py, config.py

Phase 2 (Alpha) adds:
  calibrate/mutator.py ──► persona/store.py (versioning)
  calibrate/loop.py ──► calibrate/mutator.py
  
Phase 3 (MVP) adds:
  validate.py ──► export/renderer.py ──► llm/ (multiple providers)
  tests/ ──► all modules
```

## Tech Stack Summary

| Concern           | Choice                    | Rationale                              |
|-------------------|---------------------------|----------------------------------------|
| Language          | Python 3.11+              | LLM tooling lingua franca              |
| HTTP              | `httpx`                   | Single dependency, async-capable, clean API |
| CLI               | `argparse`                | stdlib, no dependency                  |
| Data classes      | `dataclasses` + `json`    | stdlib, no pydantic needed at this scale |
| Storage           | JSON files                | No database, no migrations, git-friendly |
| Terminal UI       | ANSI escape codes         | No curses/rich dependency for POC/Alpha. Consider `rich` for MVP if warranted |
| Testing           | `pytest`                  | Standard, minimal                      |
| Config            | Environment variables     | No config files to manage              |

**Total external dependencies at MVP:** `httpx`, `pytest` (dev only). That's it.
