# Persona Forge -- Design Documents

## What Is This?

Persona Forge is a CLI tool that generates, calibrates, and exports AI personas for use as system prompts in AI coding assistants (Claude Code, ChatGPT, Copilot, etc.). You describe yourself through a structured interview, then the system iteratively refines a persona profile through a human-in-the-loop calibration loop until it consistently captures your voice, priorities, and decision-making style.

The output is a system prompt you can paste into your AI coding tool so it answers questions the way *you* would.

## Document Index

| Document | What It Covers |
|----------|---------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System architecture, component map, data flow contracts, design principles |
| [DATA-MODEL.md](./DATA-MODEL.md) | Persona JSON schema, trait structure, state file format, versioning rules |
| [CALIBRATION-LOOP.md](./CALIBRATION-LOOP.md) | Outer/inner loop mechanics, question generation strategy, trait mutation, human interaction model, fatigue management |
| [EVALUATION.md](./EVALUATION.md) | 4-dimension scoring system, LLM evaluation prompts, human quick-ratings, blind comparison tests, regression testing |
| [PROMPTS.md](./PROMPTS.md) | Every LLM prompt template in the system, organized by phase (seed, calibrate, evaluate, export) |
| [CLI-DESIGN.md](./CLI-DESIGN.md) | All CLI commands with examples, flags, environment variables, user flow walkthroughs |
| [INTEGRATION.md](./INTEGRATION.md) | Export formats (full/compact/one-liner), deployment targets (Claude Code, ChatGPT, Copilot, API), model tier strategy, validation pipeline |
| [PHASES.md](./PHASES.md) | POC to MVP implementation plan with file-level breakdown, day-by-day schedule, success criteria per phase |

## Reading Order

1. **Start with [ARCHITECTURE.md](./ARCHITECTURE.md)** -- understand the component structure and data flow
2. **Then [DATA-MODEL.md](./DATA-MODEL.md)** -- understand the persona representation
3. **Then [CALIBRATION-LOOP.md](./CALIBRATION-LOOP.md)** -- the core algorithm
4. **Then [EVALUATION.md](./EVALUATION.md)** -- how quality is measured
5. **[PROMPTS.md](./PROMPTS.md)** and **[CLI-DESIGN.md](./CLI-DESIGN.md)** as needed
6. **[INTEGRATION.md](./INTEGRATION.md)** -- how the output gets deployed
7. **[PHASES.md](./PHASES.md)** -- when to implement what

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Persona representation | Structured JSON, not plain text | Enables targeted mutation, diffing, versioning, multi-format export |
| Training mechanism | Prompt refinement, not fine-tuning | Works across any LLM, no training infrastructure, iterates in minutes |
| Human role | In-the-loop (approve/reject), not out-of-loop | Human is the ground truth; automated optimization without the human is meaningless |
| Calibration rounds | Hard cap at 4 per session | Diminishing returns beyond 4; prevents fatigue-driven quality degradation |
| Starting complexity | 8 core traits, expand as needed | Fewer well-calibrated traits beat many uncalibrated ones |
| LLM abstraction | Multi-provider with auto-detect fallback | Bedrock -> Ollama -> Anthropic chain; works without explicit configuration |
| Storage | JSON files, no database | Sufficient for the use case; git-friendly; zero infrastructure |
| Dependencies | httpx + pytest only | Minimize dependency surface; stdlib covers everything else |
