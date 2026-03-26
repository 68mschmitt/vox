# Integration & Export

## Overview

The entire point of the calibration loop is to produce a system prompt that makes an AI coding assistant behave like the calibrated persona. This document defines the export formats, deployment targets, and validation strategy.

## Export Formats

Three export tiers, all rendered from the same structured persona data.

### Full Export (1200-2000 tokens)

For tools with generous system prompt support: Claude Code (CLAUDE.md), ChatGPT custom instructions, direct API usage.

**Template structure:**

```markdown
You are {name}, a {role} with {years_experience} years of experience. {background}

## Your Values (ranked)
{for value in values}
- {value}
{end}

## How You Communicate
{communication_tone.value}. {humor.value if humor != 'none'}. {response_patterns.structure}. {response_patterns.length_preference}.

## How You Make Decisions
{for heuristic in decision_heuristics}
- {heuristic}
{end}

## Your Technical Philosophy
{tool_philosophy.value}. {tech_preferences.philosophy}.
Preferred stack: {tech_preferences.languages}, {tech_preferences.frameworks}, {tech_preferences.tools}.

## Your Personality
{for quirk in personality_quirks}
- {quirk}
{end}

## What Frustrates You
{for f in frustrations}
- {f}
{end}

## What You Never Do
{for ap in anti_patterns}
- {ap}
{end}

## Examples of Your Voice

{for exemplar in golden_exemplars[:3]}
**Q: {exemplar.question}**
A: {exemplar.human_answer}

{end}

## Important
Answer all questions as {name}. Let your biases and preferences show. Be direct and opinionated. If you'd push back on something, push back. You are not a generic AI assistant — you are a specific person with specific views.
```

### Compact Export (~600 tokens)

For tools with tighter context windows or where the persona shares space with other system prompt content.

**Template structure:**

```markdown
You are {name}, a {role}. {background_one_sentence}.

Core values: {values[:3] joined}.
Communication: {communication_tone.value}. {humor.value if humor != 'none'}.
Decisions: {decision_heuristics[:2] joined}.
Tech philosophy: {tool_philosophy.value}.
Never: {anti_patterns[:2] joined}.

Example:
Q: {golden_exemplars[0].question}
A: {golden_exemplars[0].human_answer}

Stay in character. Be opinionated. Answer as {name}, not as a generic assistant.
```

### One-Liner (~100 tokens)

For prepending to an existing system prompt or tools with minimal customization.

**Template:**

```
You are {name}, a {role} who values {values[0]} and {values[1]}, communicates in a {communication_tone.value} manner, and believes {decision_heuristics[0]}.
```

## Deployment Targets

### Claude Code / OpenCode

**Integration point:** Project-level CLAUDE.md or system prompt configuration.

**Steps:**
1. Export full format to `{persona_name}.claude.md`
2. User copies content into their `.claude/CLAUDE.md` or project instructions
3. Or: export directly to the target file with `--target claude-code --path /path/to/project`

**Claude-specific notes:**
- Claude has strong system prompt adherence, so the full export works well as-is
- The "Important" section at the end reinforces character consistency, which Claude respects
- Golden exemplars are particularly effective with Claude for anchoring voice

### ChatGPT Custom Instructions

**Integration point:** Settings > Personalization > Custom Instructions

**Steps:**
1. Export compact format (ChatGPT has a shorter custom instructions limit)
2. User pastes into the "How would you like ChatGPT to respond?" field

**ChatGPT-specific notes:**
- Custom instructions have a ~1500 character limit, so compact format is the default
- ChatGPT tends toward verbosity; add an explicit "Be concise" instruction
- Reduce golden exemplars to 1 for token efficiency

### Copilot

**Integration point:** `.github/copilot-instructions.md` or IDE settings

**Steps:**
1. Export compact format
2. Place in repo root as `.github/copilot-instructions.md`

**Copilot-specific notes:**
- Copilot's persona adherence is less consistent than Claude's
- Use more directive language ("Always...", "Never...")
- Emphasize code-level traits (naming conventions, comment style, pattern preferences)

### Direct API Usage

**Integration point:** System message in API calls

**Steps:**
1. Export full format as a string
2. User includes it as the `system` parameter in their API calls

**API-specific notes:**
- This is the most flexible deployment target
- Full export works for all major providers
- Temperature setting matters: recommend 0.7 for persona consistency (lower = more predictable but less personality; higher = more creative but more likely to break character)

## Model Capability Tiers

Different models need different export strategies. The system detects or is told the target model and adjusts accordingly.

### Tier 1: High Capability (Claude 3.5+ via Bedrock or direct API, GPT-4, Gemini Pro)

- Full export, all traits, all nuance
- Subtle trait descriptions work ("dry humor with self-deprecating undertones")
- 3 golden exemplars
- Minimal behavioral guardrails needed

### Tier 2: Medium Capability (GPT-3.5, Claude Haiku, smaller models)

- Compact export with modifications
- Replace subtle traits with explicit behavioral instructions
  - Instead of: "dry humor with self-deprecating undertones"
  - Use: "Occasionally make a joke at your own expense. Keep humor brief."
- 1 golden exemplar
- Add more explicit "do/don't" lists
- Reduce anti_patterns to the 2 most important

### Tier 3: Local / Small Models (Ollama with 7B-13B)

- One-liner + 1 exemplar
- Extremely direct instructions only
- Remove nuance that small models will ignore or misinterpret
- Focus on the 3 most distinctive traits

## Validation Pipeline

After export, the system validates the persona against the target model.

### Validation Flow

```
1. Export persona to target format
2. Select 3 questions from golden exemplars + 2 fresh questions
3. Generate answers using the exported prompt on the TARGET model
4. Score answers against human reference answers
5. Report:
   - Per-question scores
   - Comparison to calibration scores (was anything lost in export?)
   - Model-specific recommendations
```

### Cross-Model Validation

When the calibration model differs from the deployment model:

```
1. Generate answers to 5 questions using:
   a. Calibration model + full persona (baseline)
   b. Deployment model + exported prompt (test)
2. Score both against human reference
3. If deployment model scores > 1.5 points lower:
   a. Identify which dimensions degraded
   b. Suggest export adjustments (more explicit instructions, different exemplars)
   c. Optionally: run 1 "model-adaptation" calibration round against the deployment model
```

### Export Report

```
Export Validation Report
━━━━━━━━━━━━━━━━━━━━━━

Persona: Eitan Katz (v7, tagged: best)
Format: Full (1,847 tokens)
Target: Claude Code (claude-3.5-sonnet)

Validation Results:
  Q1 - Architecture decision:  8.2 (calibration: 8.5)  ✓
  Q2 - Code review:            7.8 (calibration: 8.1)  ✓
  Q3 - Team conflict:          8.5 (calibration: 8.3)  ✓
  Q4 - Tool selection:         7.1 (calibration: 7.5)  ✓
  Q5 - Debugging approach:     7.9 (calibration: 8.0)  ✓

Overall: 7.9 (calibration: 8.1, delta: -0.2)

Status: PASS (delta within acceptable range)

Export saved to: personas/eitan-katz/exports/full.md
```

## Export CLI Commands

```bash
# Export current best version, full format (uses auto-detected provider)
persona-forge export eitan-katz

# Export specific version, compact format
persona-forge export eitan-katz --version 5 --format compact

# Export with validation against a specific provider
persona-forge export eitan-katz --validate --provider bedrock

# Export directly to Claude Code project
persona-forge export eitan-katz --target claude-code --path ~/projects/myapp

# Export all formats at once
persona-forge export eitan-katz --all-formats

# Cross-model validation (e.g., calibrate locally, deploy to Bedrock)
persona-forge validate eitan-katz --calibration-provider ollama --deployment-provider bedrock
```
