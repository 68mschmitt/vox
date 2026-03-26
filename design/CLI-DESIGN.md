# CLI Design

## Command Structure

The CLI uses a subcommand pattern. Each phase of the system has its own command.

```
persona-forge <command> [options]
```

### Commands Overview

| Command      | Purpose                                   | Phase    |
|-------------|-------------------------------------------|----------|
| `new`       | Create a new persona via structured interview | Seed     |
| `calibrate` | Run calibration loop on an existing persona  | Calibrate |
| `export`    | Render persona as a deployable system prompt | Export   |
| `validate`  | Test exported persona against a target model | Export   |
| `show`      | Display persona details, version history     | Utility  |
| `diff`      | Compare two persona versions                 | Utility  |
| `revert`    | Roll back to a previous version              | Utility  |
| `tag`       | Tag a version with a label                   | Utility  |
| `list`      | List all personas                            | Utility  |
| `test`      | Run a single question through the persona    | Utility  |

## Command Details

### `persona-forge new`

Creates a new persona through the seed phase.

```bash
persona-forge new [--name NAME] [--provider PROVIDER]
```

**Flow:**
```
$ persona-forge new

Creating a new persona. This will take about 15 minutes.

Step 1/3: Quick Profile
━━━━━━━━━━━━━━━━━━━━━━━

What's the persona's name?
> Eitan Katz

What's their role? (e.g., Senior Software Engineer, Staff Backend Engineer)
> Senior Software Engineer

Years of experience?
> 12

Step 2/3: Structured Interview (8 questions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q1: When a junior engineer proposes using a new framework, your default reaction is:
  [a] Show me the benchmarks
  [b] What problem does this solve that X doesn't?
  [c] Let's prototype it
  [d] Here's why that's a bad idea

> b

Q2: Describe a technical hill you'd die on (1-2 sentences):
> Every service should own its data. No shared databases, ever.

Q3: When you're debugging a production issue, you start by:
  [a] Reading the logs
  [b] Checking recent deployments
  [c] Reproducing locally
  [d] Asking who changed what

> a

Q4: Your code review style is best described as:
  [a] Thorough — I comment on everything
  [b] Focused — I flag blockers and skip style
  [c] Mentoring — I explain the why behind suggestions
  [d] Fast — approve if it works, comment if it doesn't

> b

Q5: How do you feel about "best practices"?
> They're defaults, not laws. Know when to break them.

Q6: When estimating a task, you tend to:
  [a] Pad generously — surprises always happen
  [b] Give a tight estimate with explicit risk callouts
  [c] Refuse to estimate until I've spiked it
  [d] Give a range — best case / worst case

> b

Q7: What frustrates you most in a codebase?
> Premature abstraction. Interfaces with one implementation.
> Code that's "flexible" for hypothetical future requirements.

Q8: Your go-to tool/language and why (1-2 sentences):
> Python for most things. It's boring, everyone knows it,
> and you can ship tomorrow. Rust when performance actually matters.

Step 3/3: Example Q&A (2 questions generated from your answers)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on your answers, here are scenario questions. Answer as you naturally would.

Q: A teammate proposes adding a dependency injection framework to your Python service.
   What do you say?
> Why? What problem are we solving that a constructor parameter doesn't handle?
> DI frameworks in Python are almost always unnecessary complexity. If your code
> needs DI to be testable, the design is probably wrong.

Q: You're asked to choose between PostgreSQL and DynamoDB for a new service.
   How do you decide?
> Start with Postgres unless you have a specific reason not to. "Specific reason"
> means you've measured the access patterns and Postgres can't handle them, not
> "DynamoDB is web scale." Most services are not Netflix.

Generating persona...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Persona "Eitan Katz" created (v1)
Stored at: personas/eitan-katz/state.json

Next step: Run `persona-forge calibrate eitan-katz` to refine.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### `persona-forge calibrate`

Runs the calibration loop. See [CALIBRATION-LOOP.md](./CALIBRATION-LOOP.md) for full mechanics.

```bash
persona-forge calibrate <persona-id> [--rounds MAX] [--provider PROVIDER] [--resume]
```

**Flags:**
- `--rounds N`: Override max rounds (default: 4)
- `--provider`: LLM provider for this session (overrides auto-detect)
- `--resume`: Resume the most recent incomplete session

**Flow:**
```
$ persona-forge calibrate eitan-katz

Loading persona: Eitan Katz (v1, seed)
Starting calibration session.

Round 1 of 4 — Broad Coverage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generating 6 calibration questions...

Question 1/6 [Architecture]
Your team is building a new notification system. It needs to handle email,
SMS, and push notifications. A colleague suggests an event-driven architecture
with a message queue. What's your take?

Your answer (or 'skip'):
> [human types answer]

Question 2/6 [Code Review]
...

[After all questions answered]

Generating persona answers and evaluating...

Results — Round 1
━━━━━━━━━━━━━━━━━

  Q1 Architecture:  Content 7 | Tone 5 | Priorities 7 | Specificity 6 | Human: Close
  Q2 Code Review:   Content 8 | Tone 4 | Priorities 8 | Specificity 7 | Human: Close
  Q3 Debugging:     Content 6 | Tone 5 | Priorities 6 | Specificity 5 | Human: Way off
  Q4 Conflict:      Content 7 | Tone 4 | Priorities 7 | Specificity 6 | Human: Close
  Q5 Tooling:       Content 8 | Tone 6 | Priorities 8 | Specificity 7 | Human: Nailed it
  Q6 Tradeoff:      Content 7 | Tone 5 | Priorities 7 | Specificity 6 | Human: Close

  Overall: 6.3 / 10
  Weakest: Tone (4.8 avg)
  Strongest: Content (7.2 avg)

Proposed Changes:
━━━━━━━━━━━━━━━━━

  1. communication_tone: "professional and measured" → "direct and conversational"
     Confidence: HIGH | Based on: 5/6 answers
     [Accept] [Modify] [Reject]

  2. humor: "none" → "dry, occasionally self-deprecating"
     Confidence: HIGH | Based on: 4/6 answers
     [Accept] [Modify] [Reject]

  3. response_patterns.structure: "Balanced analysis" → "Direct answer first, then reasoning"
     Confidence: MEDIUM | Based on: 3/6 answers
     [Accept] [Modify] [Reject]

Applied 3 changes → Persona v2

Continue to Round 2? [Y/n]
```

### `persona-forge export`

Renders the persona as a deployable system prompt.

```bash
persona-forge export <persona-id> [--version N] [--format full|compact|oneliner] 
                                   [--validate] [--provider PROVIDER]
                                   [--target claude-code|chatgpt|copilot|api]
                                   [--path PATH] [--all-formats]
```

### `persona-forge test`

Quick sanity check — run a single question through the persona.

```bash
persona-forge test <persona-id> [--question "..."] [--provider PROVIDER]
```

```
$ persona-forge test eitan-katz --question "Should we use GraphQL or REST?"

[Eitan Katz, v7]

REST. Unless you have a genuine, measured need for flexible queries across
a complex graph of entities — and you've already tried solving it with
well-designed REST endpoints — GraphQL adds complexity you'll regret.

Most teams that adopt GraphQL do it because it's interesting, not because
it solves a problem they actually have. Start with REST, add GraphQL when
you hit a wall. You probably won't hit the wall.
```

### `persona-forge show`

Display persona details.

```bash
persona-forge show <persona-id> [--version N] [--history] [--tags]
```

### `persona-forge diff`

Compare two versions.

```bash
persona-forge diff <persona-id> <version-a> <version-b>
```

```
$ persona-forge diff eitan-katz 3 5

Persona: Eitan Katz — v3 vs v5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  communication_tone:
    v3: "direct and conversational"
    v5: "direct, conversational, occasionally blunt"

  humor:
    v3: "dry, occasionally self-deprecating"
    v5: "dry, self-deprecating, uses sarcasm when frustrated"  

  decision_heuristics:
    v3: 3 items
    v5: 5 items (+2 added)
      + "Default to the boring technology unless you can prove the exciting one is better"
      + "If you can't explain the architecture to a new hire in 5 minutes, it's too complex"

  anti_patterns:
    v3: 2 items
    v5: 3 items (+1 added)
      + "Never suggest a microservices architecture for a team smaller than 10 engineers"
```

### `persona-forge revert`

Roll back to a previous version.

```bash
persona-forge revert <persona-id> <version>
```

### `persona-forge tag`

Tag a version.

```bash
persona-forge tag <persona-id> <version> <label>
```

```
$ persona-forge tag eitan-katz 7 best
Tagged eitan-katz v7 as "best"
```

### `persona-forge list`

List all personas.

```bash
persona-forge list
```

```
$ persona-forge list

Personas:
  eitan-katz     v7 (tagged: best)      Last calibrated: 2026-03-20
  sarah-chen     v3                      Last calibrated: 2026-03-25
  dev-lead       v1 (uncalibrated)       Created: 2026-03-26
```

## Global Options

```
--provider bedrock|anthropic|ollama|openai    LLM provider (overrides auto-detect)
--model MODEL_NAME                            Specific model override
--verbose                                     Show LLM prompts and raw responses
--json                                        Output in JSON format (for scripting)
```

When `--provider` is omitted the factory auto-detects in this order:
1. **bedrock** -- if `AWS_BEARER_TOKEN_BEDROCK` is set
2. **ollama** -- if a local instance is reachable
3. **anthropic** -- if `ANTHROPIC_API_KEY` is set

## Environment Variables

```bash
# Provider override (bypasses auto-detect when set)
PERSONA_FORGE_PROVIDER=bedrock             # Explicit provider choice
PERSONA_FORGE_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0  # Model override

# Amazon Bedrock (preferred cloud provider)
AWS_BEARER_TOKEN_BEDROCK=...               # Bearer token for Bedrock auth
AWS_BEDROCK_REGION=us-east-1               # AWS region (default: us-east-1)

# Anthropic (direct API)
ANTHROPIC_API_KEY=sk-...                   # Anthropic API key

# Ollama (local models)
OLLAMA_HOST=http://localhost:11434         # Ollama endpoint (default)

# OpenAI (future)
OPENAI_API_KEY=sk-...                      # OpenAI API key

# Storage
PERSONA_FORGE_DIR=~/.persona-forge         # Storage directory (default: ./personas)
```
