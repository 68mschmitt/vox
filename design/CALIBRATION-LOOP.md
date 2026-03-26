# Calibration Loop

## Overview

The calibration loop is the core value proposition of the system. It takes a first-draft persona and iteratively refines it through human-in-the-loop feedback until the persona consistently produces answers that match the human's voice, priorities, and decision-making style.

The loop is essentially gradient descent on persona space, where the human is the loss function.

## Loop Structure

The calibration process has two nested loops:

```
┌─────────────────────────────────────────────────────┐
│ Outer Loop (Session)                                │
│ Manages rounds, tracks convergence, handles escape  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Inner Loop (Round)                            │  │
│  │ Generate questions → Collect answers →         │  │
│  │ Evaluate → Propose changes → Human reviews    │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  Convergence check after each round                 │
│  Stall detection after 2+ rounds                    │
│  Hard cap at 4 rounds per session                   │
└─────────────────────────────────────────────────────┘
```

### Outer Loop (Session)

A session is a single calibration sitting. The human starts a session, goes through multiple rounds, and either reaches convergence or hits the round cap.

**Session flow:**

1. Load current persona version
2. Enter Round 1
3. After each round, check convergence criteria
4. If converged: suggest finishing, export
5. If stalled: suggest overhaul or finish
6. If round cap (4) reached: force finish with option to start new session
7. Save session to state

**Convergence criteria:**
- Overall score >= 8.0 for 2 consecutive rounds across all questions
- OR the human manually declares "good enough"

**Stall detection:**
- Score improvement < 0.3 between consecutive rounds after round 2
- OR a trait has oscillated (changed direction) in the last 2 rounds

### Inner Loop (Round)

A single round of calibration. This is where the actual work happens.

**Round flow:**

```
Step 1: Generate Questions
    │
    ├── Round 1: Broad coverage (5-7 questions across domains)
    │   - Architecture decisions
    │   - Code review scenarios
    │   - Debugging approach
    │   - Team disagreement
    │   - Tool/framework selection
    │
    ├── Round 2+: Adaptive focus (5-7 questions targeting weak areas)
    │   - Weighted toward categories with lowest scores
    │   - Increased specificity (edge cases, nuanced scenarios)
    │   - At least 1 question from a previously-strong area (regression check)
    │
    ▼
Step 2: Human Answers Questions
    │
    ├── Human sees question, writes their answer
    ├── NO persona answer shown yet (prevents anchoring)
    ├── Human can skip questions (optional)
    │
    ▼
Step 3: Generate Persona Answers
    │
    ├── Each question answered by LLM using current persona
    ├── Answers generated independently (no cross-contamination)
    │
    ▼
Step 4: Evaluate Divergence
    │
    ├── Side-by-side display: human answer vs persona answer
    ├── LLM-based scoring on 4 dimensions (see EVALUATION.md)
    ├── Human quick-rates each pair: "Nailed it" / "Close" / "Way off"
    ├── Human highlights specific issues on "Close" / "Way off" answers
    │
    ▼
Step 5: Propose Trait Changes
    │
    ├── Mutator analyzes divergence report
    ├── Generates batch change proposal (multiple traits at once)
    ├── Each change includes: trait, from, to, confidence, rationale
    ├── Checks trait change log for oscillation before proposing
    │
    ▼
Step 6: Human Reviews Changes
    │
    ├── Human sees each proposed change
    ├── Accepts, rejects, or modifies each one
    ├── Accepted changes create new persona version
    ├── Golden exemplars updated if any Q&A pairs scored >= 8.5
    │
    ▼
Step 7: Round Summary
    │
    ├── Score comparison: this round vs previous
    ├── Progress visualization
    ├── Convergence check
    └── Prompt: continue to next round, or finish?
```

## Question Generation Strategy

### Round 1: Broad Coverage

The first round casts a wide net to identify where the persona diverges from the human. Questions cover 5-7 distinct scenario types:

| Category              | Example Question                                                                                    |
|-----------------------|-----------------------------------------------------------------------------------------------------|
| Architecture Decision | "Your team needs to choose between a monolith and microservices for a new product. What do you advocate for and why?" |
| Code Review           | "You're reviewing a PR that introduces a new ORM. The code works but adds a dependency. What's your feedback?" |
| Debugging             | "Production is down, logs show intermittent 500s on the auth service. Walk through your first 5 minutes." |
| Team Conflict         | "A junior engineer wants to rewrite a working service in Rust. How do you respond?"                 |
| Tool Selection        | "You need to pick a CI/CD platform for a new project. What do you choose and what's non-negotiable?" |
| Tradeoff Framing      | "A PM asks you to estimate: 2 weeks for a clean solution or 3 days for a hack. How do you frame the tradeoff?" |
| Philosophy            | "What's a technical opinion you hold that most engineers would disagree with?"                      |

Questions are generated by the LLM using the persona's identity and tech preferences as context, ensuring they are relevant to the persona's domain.

### Round 2+: Adaptive Focus

After Round 1, the system knows which scoring dimensions and question categories revealed the most divergence. Subsequent rounds:

1. **Weight toward weak areas.** If tone scores were low across the board, generate more questions that specifically test communication style (e.g., conflict scenarios, code review feedback).

2. **Increase specificity.** Replace broad scenarios with narrow, opinionated ones. "How do you handle a PR with 47 files?" is more revealing than "How do you do code review?"

3. **Include 1-2 regression checks.** Re-test a previously-strong area to ensure trait changes haven't degraded other dimensions.

4. **Adversarial questions (Round 3+).** Generate questions specifically designed to break character. If the persona is calibrated as "direct and blunt," ask a question where most people would be diplomatic and see if the persona stays in character.

### Question Adaptation Algorithm

```
Input: previous_round_scores, trait_change_log, question_history
Output: weighted_focus_areas

1. Rank scoring dimensions by average score (ascending)
2. Map low-scoring dimensions to question categories:
   - Low content  → architecture, tool selection, philosophy
   - Low tone     → conflict, code review, tradeoff framing
   - Low priorities → architecture, debugging, tradeoff framing
   - Low specificity → debugging, tool selection, code review
3. Assign question count per category:
   - Weakest 2 categories: 2 questions each
   - Next weakest: 1 question
   - Regression check: 1 question from strongest category
   - Wild card: 1 adversarial question (Round 3+ only)
4. Filter out questions too similar to recent history (cosine similarity check)
```

## Trait Mutation Strategy

### Batch Changes with Human Approval

After evaluation, the mutator proposes a batch of trait changes rather than one-at-a-time. This is critical for efficiency -- if the persona is off on 3 dimensions, fixing one per round means 3+ rounds before the basics are right.

**Change proposal format:**

```
Round 2 Proposed Adjustments:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. communication_tone: "professional and measured" → "direct and conversational"
   Confidence: HIGH (divergence in 4/5 answers)
   Rationale: Human consistently uses shorter sentences, contractions,
   and addresses the reader directly. Persona is too formal.

2. risk_tolerance: "conservative" → "moderate, with bias toward simplicity"
   Confidence: MEDIUM (divergence in 2/5 answers)
   Rationale: Human advocated for the simpler solution even when it wasn't
   the safest choice. Current persona over-indexes on risk avoidance.

3. humor: "none" → "dry, occasionally self-deprecating"
   Confidence: HIGH (divergence in 3/5 answers)
   Rationale: Human used humor in 3 answers to soften direct opinions.
   Persona is humorless, making it sound robotic.

4. technical_depth: NO CHANGE
   Rationale: Depth level matched well across all answers.

[Accept All] [Review Each] [Reject All]
```

### Oscillation Prevention

The trait change log is checked before every proposal:

```
For each proposed change:
  1. Look up trait in change_log for last 3 versions
  2. If trait changed direction (e.g., more formal → less formal → more formal):
     a. Flag: "This trait may be context-dependent"
     b. Propose splitting into context-specific variants
     c. Example: risk_tolerance → risk_tolerance_architecture + risk_tolerance_tooling
  3. If trait was changed and then reverted:
     a. Revert to the version before the first change
     b. Lock the trait for this round (exclude from proposals)
```

### Score Regression Handling

After applying changes, if the overall score drops compared to the previous round:

1. Identify which trait changes correlated with score drops
2. Offer to revert specific changes (not the whole batch)
3. If total regression > 1.0 point, auto-suggest reverting to previous version

### Overhaul Escape Hatch

When incremental adjustments stall (stall detected after 2+ rounds of <0.3 improvement):

1. Gather all golden exemplars + best Q&A pairs from all rounds
2. Gather the accumulated trait change log
3. Feed both to the persona generator with an "overhaul" prompt
4. Generate a new persona from scratch, informed by everything learned
5. This becomes a new version with source: "overhaul"
6. Resume calibration from this new base

## Human Interaction Design

### Fatigue Management

The calibration loop is designed to respect human attention:

1. **Hard cap at 4 rounds per session.** Even if not converged, stop and let the human come back later.

2. **Progress visualization after every round.** Show a concrete number going up. "Persona alignment: 62% → 78%." This keeps the human engaged.

3. **Reduce human effort over rounds:**
   - Round 1: Human writes full answers (most effort)
   - Round 2: Human writes answers only for new question types; reviews persona answers for repeated categories
   - Round 3+: Review-only mode. Human rates persona answers and flags specific issues. No more writing full answers (sufficient reference material exists).

4. **Skip allowed.** Any question can be skipped. Forced completionism kills engagement.

5. **Save and resume.** Session state is persisted after every round. The human can quit and resume later with full context.

### Time Budget Per Round

| Round | Human Effort         | Expected Time |
|-------|---------------------|---------------|
| 1     | Answer 5-7 questions + rate persona answers | 15-20 min |
| 2     | Answer 3-5 questions + rate persona answers | 10-15 min |
| 3     | Review-only + flag issues | 5-10 min |
| 4     | Review-only (if needed)  | 5 min |

**Total calibration time target: 35-50 minutes across all rounds.**

## Calibration Parameters

These constants control the loop behavior. All are configurable via `config.py`.

```python
# Scoring
CONVERGENCE_THRESHOLD = 8.0       # Overall score to declare convergence
CONVERGENCE_ROUNDS = 2            # Consecutive rounds above threshold to converge
GOLDEN_EXEMPLAR_THRESHOLD = 8.5   # Score to auto-add to golden exemplars
MAX_GOLDEN_EXEMPLARS = 5          # Cap on golden exemplar count

# Loop control
MAX_ROUNDS_PER_SESSION = 4        # Hard cap on rounds
STALL_THRESHOLD = 0.3             # Minimum score improvement to avoid stall detection
STALL_ROUNDS = 2                  # Consecutive stall rounds before overhaul suggestion

# Mutation
MAX_TRAIT_CHANGES_PER_ROUND = 4   # Don't change more than 4 traits at once
REGRESSION_REVERT_THRESHOLD = 1.0 # Score drop that triggers auto-revert suggestion
OSCILLATION_LOOKBACK = 3          # Versions to check for oscillation

# Questions
QUESTIONS_PER_ROUND = 6           # Default question count (5-7 range)
REGRESSION_QUESTIONS = 1          # Questions from strong areas per round
ADVERSARIAL_ROUND_START = 3       # Round to start including adversarial questions
```
