# Evaluation

## Overview

Evaluation is the mechanism that tells the calibration loop whether the persona is improving. It operates on two levels:

1. **Per-question scoring** -- How well did the persona's answer match the human's on each question?
2. **Cross-round tracking** -- Is the persona converging toward the human's voice over time?

The evaluation combines LLM-based analysis with human quick-ratings to produce actionable divergence reports.

## Scoring Dimensions

Each question-answer pair is scored on 4 orthogonal dimensions, each on a 1-10 scale:

### Content (what is said)
Does the persona's answer cover the same technical ground as the human's? Does it reach the same conclusions? Does it recommend the same approaches?

| Score | Meaning |
|-------|---------|
| 1-3   | Fundamentally different recommendation or conclusion |
| 4-5   | Same general direction but different specifics |
| 6-7   | Same recommendation with minor differences in detail |
| 8-9   | Nearly identical technical content |
| 10    | Indistinguishable content |

### Tone (how it is said)
Does the persona's answer sound like the human? Sentence structure, formality level, use of humor, hedging vs. directness, warmth vs. clinical.

| Score | Meaning |
|-------|---------|
| 1-3   | Completely different voice (e.g., formal vs. casual) |
| 4-5   | Similar register but noticeably different personality |
| 6-7   | Mostly right voice with occasional breaks |
| 8-9   | Consistent voice match with minor tells |
| 10    | Indistinguishable voice |

### Priorities (what is emphasized)
When the human and persona both cover multiple points, do they emphasize the same things? What does each put first? What do they spend the most words on?

| Score | Meaning |
|-------|---------|
| 1-3   | Different primary concern entirely |
| 4-5   | Same concerns but different ordering |
| 6-7   | Same top priority, different secondary ordering |
| 8-9   | Nearly identical priority structure |
| 10    | Identical emphasis pattern |

### Specificity (how detailed)
Does the persona provide the same level of detail as the human? Does it use concrete examples where the human does? Does it stay abstract when the human stays abstract?

| Score | Meaning |
|-------|---------|
| 1-3   | Vastly different detail level (e.g., abstract vs. concrete code) |
| 4-5   | Similar scope but different depth |
| 6-7   | Matching depth with different example choices |
| 8-9   | Matching depth and similar example patterns |
| 10    | Indistinguishable specificity |

### Overall Score
Weighted average of the 4 dimensions:

```
overall = (content * 0.30) + (tone * 0.30) + (priorities * 0.25) + (specificity * 0.15)
```

Content and tone are weighted equally and highest because they are the most observable dimensions. Priorities matter but are subtler. Specificity is the least critical -- it's easier to adjust with simple instructions.

## Evaluation Pipeline

### Step 1: LLM-Based Scoring

For each question, the evaluator LLM receives:

```
System: You are an expert at analyzing writing style and personality consistency.

User:
QUESTION: {question_text}

HUMAN ANSWER:
{human_answer}

PERSONA ANSWER:
{persona_answer}

Score the persona's answer against the human's on these 4 dimensions (1-10 each):
1. Content: Do they say the same thing?
2. Tone: Do they sound the same?
3. Priorities: Do they emphasize the same things?
4. Specificity: Do they provide the same level of detail?

For each dimension:
- Provide the numeric score
- Provide a 1-sentence explanation of the gap (if any)
- Identify the specific trait that would need to change to close the gap

Return as JSON.
```

Output format:

```json
{
  "content": {
    "score": 7,
    "gap": "Persona recommended microservices; human advocated for a modular monolith.",
    "trait_signal": "Persona's architecture bias skews toward distributed systems"
  },
  "tone": {
    "score": 5,
    "gap": "Human uses casual language and humor; persona is clinical and formal.",
    "trait_signal": "communication_tone needs to shift toward conversational"
  },
  "priorities": {
    "score": 8,
    "gap": "Both prioritize simplicity, but human puts team velocity first.",
    "trait_signal": "values ordering may need adjustment"
  },
  "specificity": {
    "score": 6,
    "gap": "Human gave a concrete Redis example; persona stayed abstract.",
    "trait_signal": "response_patterns.code_vs_prose needs more concrete examples"
  }
}
```

### Step 2: Human Quick-Rating

After seeing the side-by-side comparison, the human provides a fast rating:

```
Question: "Your team is debating Redis vs. an in-process cache..."

YOUR ANSWER:                          PERSONA'S ANSWER:
"Honestly, for 100 req/s just use    "I'd recommend evaluating the trade-
an in-process cache. Redis is great   offs between Redis and an in-process
but you don't need it yet. Ship       cache. Given the request volume of
the simple thing, add Redis when      100 req/s, an in-process solution
you actually hit scaling problems."   would be sufficient for the current
                                      requirements..."

How did the persona do?
  [1] Nailed it    [2] Close but off    [3] Way off

> 2

What's off? (brief):
> Too formal, sounds like a consultant not an engineer. I'd never say
> "evaluating the trade-offs" or "current requirements"
```

The human quick-rating serves as a calibration signal for the LLM scores. If the LLM gave tone an 8 but the human said "Way off" on tone, the system adjusts the effective score downward.

### Step 3: Score Reconciliation

```python
def reconcile_scores(llm_scores: dict, human_rating: str, human_notes: str) -> dict:
    """
    Adjust LLM scores based on human feedback.
    
    - "Nailed it": LLM scores used as-is, floor of 7 on all dimensions
    - "Close but off": LLM scores used, but dimensions mentioned in 
      human_notes get a -1 penalty (human noticed something LLM missed)
    - "Way off": LLM scores capped at 5 on all dimensions; 
      dimensions mentioned in notes capped at 3
    """
```

This reconciliation prevents the known LLM-as-judge bias toward generous scoring.

## Advanced Evaluation Techniques

### Blind Comparison Test (Round 2+)

For 1-2 questions per round, generate two answers to the same question:
1. One from the persona
2. One from a generic LLM prompt (no persona instructions)

Present both to the evaluator LLM (without labels) and ask:

```
Two engineers answered the same question. Based on the reference human answer,
which response (A or B) more closely matches the human's style and personality?
Explain your reasoning.
```

If the evaluator can't distinguish the persona answer from the generic one, the persona isn't distinctive enough. This triggers a flag in the divergence report.

### Cross-Question Consistency Check

After scoring all questions in a round, run a meta-evaluation:

```
Here are 5 answers written by the same persona:
[Answer 1]
[Answer 2]
...

Do these all sound like they came from the same person? Rate consistency 1-10.
Identify any answers that feel like a different personality.
```

A persona can score well on individual questions but lack coherence across questions. This check catches that. A consistency score below 7 triggers a "coherence" flag in the divergence report.

### Regression Testing (Round 3+)

After each persona change, silently re-generate answers to the 2-3 highest-scoring Q&A pairs from previous rounds. Compare the new persona answers against the previously high-scoring ones.

If any previously-good answer degrades by more than 1.5 points, flag it:

```
WARNING: Regression detected
Question: "How do you handle a PR with 47 files?"
Previous score: 8.5 (v3) → Current score: 6.8 (v4)
Likely cause: communication_tone change in v4
```

This prevents the common failure mode where fixing one dimension breaks another.

## Divergence Report

After evaluation, the system produces a structured divergence report that feeds the trait mutator.

```json
{
  "round": 2,
  "overall_score": 6.8,
  "score_delta": "+1.2 from round 1",
  "convergence_status": "improving",
  
  "dimension_averages": {
    "content": 7.5,
    "tone": 5.2,
    "priorities": 7.8,
    "specificity": 6.5
  },
  
  "weakest_dimension": "tone",
  "strongest_dimension": "priorities",
  
  "per_question": [
    {
      "question_id": "q1",
      "scores": {"content": 8, "tone": 5, "priorities": 8, "specificity": 7},
      "human_rating": "close_but_off",
      "human_notes": "Too formal, sounds like a consultant",
      "trait_signals": ["communication_tone → more casual", "humor → add dry humor"]
    }
  ],
  
  "blind_test_result": {
    "ran": true,
    "persona_identified": true,
    "distinction_confidence": "medium"
  },
  
  "consistency_score": 8.2,
  
  "regressions": [],
  
  "trait_signals_aggregated": [
    {"trait": "communication_tone", "direction": "more casual", "signal_count": 4, "confidence": "high"},
    {"trait": "humor", "direction": "add dry/self-deprecating", "signal_count": 3, "confidence": "high"},
    {"trait": "specificity", "direction": "more concrete examples", "signal_count": 2, "confidence": "medium"}
  ]
}
```

## Evaluation Parameters

```python
# Scoring weights
CONTENT_WEIGHT = 0.30
TONE_WEIGHT = 0.30
PRIORITIES_WEIGHT = 0.25
SPECIFICITY_WEIGHT = 0.15

# Human rating adjustments
NAILED_IT_FLOOR = 7           # Minimum score when human says "Nailed it"
CLOSE_BUT_OFF_PENALTY = 1     # Penalty for dimensions mentioned in notes
WAY_OFF_CAP = 5               # Max score when human says "Way off"
WAY_OFF_MENTIONED_CAP = 3     # Max for specifically mentioned dimensions

# Advanced checks
BLIND_TEST_FREQUENCY = 2      # Questions per round for blind comparison
CONSISTENCY_WARNING = 7.0      # Below this triggers coherence flag
REGRESSION_THRESHOLD = 1.5     # Score drop to trigger regression warning

# Convergence
CONVERGENCE_SCORE = 8.0        # Overall score target
CONVERGENCE_ROUNDS = 2         # Consecutive rounds needed
```
