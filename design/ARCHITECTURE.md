# Architecture

## System Overview

Persona Forge is a CLI tool that generates, calibrates, and exports AI personas for use as system prompts in AI coding assistants. The system operates in three distinct phases:

1. **Seed** -- Collect human input, generate a first-draft persona
2. **Calibrate** -- Iterative human-in-the-loop refinement loop
3. **Export** -- Render calibrated persona as a deployable system prompt

```
                         Phase 1: Seed
                    ┌─────────────────────┐
                    │  Structured Interview│
                    │  + Example Q&A Pairs │
                    └─────────┬───────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Persona Generator   │
                    │  (LLM-powered)       │
                    └─────────┬───────────┘
                              │
                              ▼
                      First-Draft Persona
                              │
                         Phase 2: Calibrate
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
    ┌──────────────────┐           ┌──────────────────┐
    │ Question Generator│           │  Human provides   │
    │ (adaptive)        │           │  reference answers │
    └────────┬─────────┘           └────────┬─────────┘
             │                              │
             ▼                              ▼
    ┌──────────────────┐           ┌──────────────────┐
    │ Persona answers   │           │  Human answers    │
    │ as-character      │           │  (ground truth)   │
    └────────┬─────────┘           └────────┬─────────┘
             │                              │
             └──────────┬───────────────────┘
                        ▼
              ┌──────────────────┐
              │   Evaluator      │
              │   (divergence    │
              │    analysis)     │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   Trait Mutator   │
              │   (propose       │
              │    adjustments)  │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   Human Review   │──── accept / reject / modify
              └────────┬─────────┘
                       │
                       ▼
                Updated Persona ──── (loop back to Question Generator)
                       │
                  Phase 3: Export
                       │
                       ▼
              ┌──────────────────┐
              │   Prompt Renderer │
              │   (full/compact/  │
              │    one-liner)     │
              └──────────────────┘
```

## Component Architecture

The system is organized into six core components with clear data contracts between them.

### Component Map

```
persona_forge/
├── main.py              # CLI entry point, argument parsing, command dispatch
├── config.py            # Constants, thresholds, provider config
├── llm/
│   ├── __init__.py      # Provider factory with auto-detect fallback chain
│   ├── provider.py      # Abstract LLM interface
│   ├── anthropic.py     # Anthropic (Claude) provider
│   ├── bedrock.py       # Amazon Bedrock provider (Converse API, bearer token auth)
│   ├── ollama.py        # Ollama (local) provider
│   ├── openai.py        # OpenAI provider
│   └── parse.py         # LLM response parsing (JSON extraction, retry logic)
├── seed/
│   ├── __init__.py
│   ├── interview.py     # Structured interview flow
│   └── generator.py     # First-draft persona generation from seed input
├── calibrate/
│   ├── __init__.py
│   ├── loop.py          # Outer calibration loop orchestration
│   ├── questions.py     # Adaptive question generation
│   ├── evaluator.py     # Divergence analysis and scoring
│   └── mutator.py       # Trait change proposal and application
├── export/
│   ├── __init__.py
│   └── renderer.py      # System prompt rendering (full/compact/one-liner)
├── persona/
│   ├── __init__.py
│   ├── model.py         # Persona data model and trait schema
│   └── store.py         # Versioned persistence (JSON file storage)
├── prompts/
│   ├── __init__.py
│   └── templates.py     # All LLM prompt templates (centralized)
└── ui/
    ├── __init__.py
    └── display.py       # Terminal output formatting and progress display
```

### Component Responsibilities

#### `llm/` -- LLM Provider Abstraction

A thin abstraction over LLM API calls. Every provider implements a single interface:

```python
class LLMProvider(Protocol):
    def generate(self, system: str, user: str, temperature: float = 0.7) -> str: ...
    def name(self) -> str: ...
```

No streaming, no tool use, no complexity. Raw prompt-in, text-out.

Provider selection uses an auto-detect fallback chain when no explicit provider is specified:

1. **Bedrock** -- if `AWS_BEARER_TOKEN_BEDROCK` is set
2. **Ollama** -- if a local Ollama instance is reachable at `localhost:11434`
3. **Anthropic** -- if `ANTHROPIC_API_KEY` is set

An explicit `--provider` flag or `PERSONA_FORGE_PROVIDER` env var bypasses the chain and uses the specified provider directly.

#### `seed/` -- Seed Input Collection

Manages the structured interview and example Q&A collection. Outputs a `SeedData` object that the generator consumes. The interview is 8-10 targeted questions (mix of multiple choice and short answer) followed by 2-3 system-generated Q&A prompts based on interview responses.

#### `calibrate/` -- Calibration Loop

The core feedback loop. Orchestrates question generation, human answer collection, persona answer generation, evaluation, and trait mutation. Each round:

1. `questions.py` generates 5-7 questions (adaptive to known weaknesses)
2. Human answers each question
3. `evaluator.py` generates persona answers and scores divergence
4. `mutator.py` proposes trait adjustments based on divergence
5. Human reviews and approves/rejects/modifies proposals
6. Updated persona feeds into next round

Hard-capped at 4 rounds before suggesting convergence. See [CALIBRATION-LOOP.md](./CALIBRATION-LOOP.md) for full mechanics.

#### `export/` -- Prompt Rendering

Takes a calibrated persona version and renders it as a deployable system prompt. Three formats:

| Format     | Token Budget | Use Case                          |
|------------|-------------|-----------------------------------|
| Full       | 1200-2000   | Claude Code, ChatGPT custom       |
| Compact    | ~600        | Tighter context windows           |
| One-liner  | ~100        | Prepend to existing system prompt  |

All formats are rendered from the same structured persona data.

#### `persona/` -- Data Model and Storage

Persona representation as structured data (not as a prompt). Versioned storage in JSON files. Every mutation creates a new version. Rollback is a pointer change. See [DATA-MODEL.md](./DATA-MODEL.md) for schema details.

#### `prompts/` -- Prompt Templates

All LLM prompt templates in a single module. Templates are plain Python string formatting -- no template engine. Each template is a function that takes structured data and returns `(system_prompt, user_prompt)` tuples. See [PROMPTS.md](./PROMPTS.md) for all templates.

#### `ui/` -- Terminal Display

Formatting for terminal output. Progress bars, side-by-side comparisons, score displays, change proposal formatting. No TUI framework -- just print statements with ANSI formatting.

## Data Flow Contracts

Components communicate through well-defined data structures. No component accesses another's internals.

```
SeedData ──────► PersonaGenerator ──────► Persona (v1)
                                              │
                                              ▼
QuestionSet ◄── QuestionGenerator ◄──── Persona (vN)
    │                                        │
    ▼                                        ▼
HumanAnswers ──► Evaluator ◄──────── PersonaAnswers
                    │
                    ▼
              DivergenceReport
                    │
                    ▼
              TraitProposal ──► HumanReview ──► Persona (vN+1)
                                                     │
                                                     ▼
                                               PromptRenderer ──► SystemPrompt (text)
```

### Key Data Types

| Type              | Description                                         | Format     |
|-------------------|-----------------------------------------------------|------------|
| `SeedData`        | Interview answers + example Q&A pairs               | dataclass  |
| `Persona`         | Structured persona traits + metadata                 | dataclass  |
| `QuestionSet`     | List of calibration questions with focus areas       | dataclass  |
| `HumanAnswers`    | Map of question_id -> human answer text              | dict       |
| `PersonaAnswers`  | Map of question_id -> persona-generated answer text  | dict       |
| `DivergenceReport`| Per-question scores + overall alignment + analysis   | dataclass  |
| `TraitProposal`   | Proposed trait changes with confidence + rationale   | dataclass  |
| `SystemPrompt`    | Rendered prompt text ready for deployment            | str        |

## Design Principles

1. **Human is the ground truth.** The system never auto-applies changes without human review. The LLM proposes, the human disposes.

2. **Structured data in, natural language out.** Personas are stored as structured JSON for mutation and versioning. They are rendered to natural language only at export time.

3. **Minimal dependencies.** Python stdlib plus one HTTP library for API calls. No frameworks, no ORMs, no template engines.

4. **Fail toward simplicity.** When in doubt, do the simpler thing. A linear 3-round calibration that produces an 80% persona is more valuable than a sophisticated adaptive system that ships late.

5. **Version everything.** Every calibration round produces a new persona version. Rollback is always one command away.

## LLM Provider Strategy

- Abstract from day one via the `LLMProvider` protocol
- Auto-detect fallback chain: Bedrock -> Ollama -> Anthropic (see `llm/__init__.py`)
- Amazon Bedrock is the preferred cloud provider (Converse API with bearer token auth)
- Ollama supported for local development with no API key needed
- Anthropic direct API as final fallback
- Validate exported personas against target deployment models
- Provider-specific quirks handled at the export layer, not the calibration layer
