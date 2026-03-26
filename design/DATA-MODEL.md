# Data Model

## Persona Schema

The persona is the central data structure. It is stored as structured JSON and rendered to natural language only at export time. This separation enables targeted mutation, clean diffing, versioning, and multi-format export.

### Core Schema

```json
{
  "id": "string (slug, e.g. 'eitan-katz')",
  "name": "string",
  "role": "string (e.g. 'Senior Software Engineer')",
  "version": "integer (monotonic, starts at 1)",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp",

  "identity": {
    "background": "string (2-3 sentences, professional background)",
    "daily_workflow": "string (what a typical day looks like)",
    "years_experience": "integer"
  },

  "traits": {
    "communication_tone": {
      "value": "string (e.g. 'direct and conversational')",
      "spectrum": ["formal", "casual"],
      "calibrated": "boolean"
    },
    "technical_depth": {
      "value": "string",
      "spectrum": ["high-level", "deep-dive"],
      "calibrated": "boolean"
    },
    "risk_tolerance": {
      "value": "string",
      "spectrum": ["conservative", "experimental"],
      "calibrated": "boolean"
    },
    "conflict_style": {
      "value": "string",
      "spectrum": ["diplomatic", "blunt"],
      "calibrated": "boolean"
    },
    "decision_making": {
      "value": "string",
      "spectrum": ["data-driven", "intuition"],
      "calibrated": "boolean"
    },
    "humor": {
      "value": "string (style description or 'none')",
      "spectrum": ["none", "frequent"],
      "calibrated": "boolean"
    },
    "teaching_approach": {
      "value": "string",
      "spectrum": ["socratic", "prescriptive"],
      "calibrated": "boolean"
    },
    "tool_philosophy": {
      "value": "string",
      "spectrum": ["proven", "cutting-edge"],
      "calibrated": "boolean"
    }
  },

  "decision_heuristics": [
    "string (e.g. 'When choosing between two approaches, pick the one with fewer dependencies')"
  ],

  "tech_preferences": {
    "languages": ["string"],
    "frameworks": ["string"],
    "tools": ["string"],
    "philosophy": "string (e.g. 'Unix tools over monolithic IDEs')"
  },

  "values": ["string (ranked, most important first)"],
  "frustrations": ["string"],
  "biases": ["string (acknowledged technical biases)"],
  "personality_quirks": ["string (2-3 specific behaviors)"],

  "response_patterns": {
    "structure": "string (e.g. 'Direct answer first, then reasoning')",
    "length_preference": "string (e.g. 'Concise unless asked for detail')",
    "code_vs_prose": "string (e.g. 'Prefers code examples over prose')"
  },

  "anti_patterns": [
    "string (things this persona would NEVER do or say)"
  ]
}
```

### Design Decisions

**Why `traits` use a structured object instead of plain strings:**
- The `spectrum` field defines the axis for that trait, enabling the mutator to propose directional changes ("move toward casual")
- The `calibrated` flag tracks which traits have been tested in the calibration loop vs. which are still defaults from the seed phase. Uncalibrated traits are lower confidence.
- The `value` field is natural language, not an enum -- it captures nuance beyond a binary spectrum position.

**Why `decision_heuristics` is a separate field:**
Decision heuristics are the highest-impact trait category for coding assistant personas. During a coding session, the persona makes dozens of micro-decisions (which pattern to use, how to structure code, when to add abstractions). These heuristics directly shape those answers. Keeping them separate from general `values` makes them easier to calibrate independently.

**Why `anti_patterns` exists:**
LLMs are better at following "do not" instructions for specific behaviors than inferring them from positive traits. If the persona should never suggest over-engineering, stating that explicitly as an anti-pattern is more reliable than hoping the LLM infers it from "values pragmatism."

### Trait Complexity Scaling

The schema starts with 8 core traits. Additional traits are added only when calibration reveals they're needed:

**When to add a new trait:**
- Oscillation detected: a trait changes direction between rounds, suggesting it's context-dependent. Split into two context-specific traits.
- Persistent gap: the human consistently says "close but not quite" and existing traits can't capture the divergence.
- The mutator proposes a new dimension that doesn't map to existing traits.

**How to add a trait:**
The mutator can propose new trait dimensions in its change proposals. The human approves the new dimension, and it's added to the schema with `calibrated: false`. The next calibration round will exercise it.

**Maximum complexity target:** 12-15 traits. Beyond that, trait interactions become unmanageable and the persona loses coherence.

## State Management

All state for a persona lives in a single JSON file per persona.

### Directory Structure

```
personas/
├── eitan-katz/
│   ├── state.json        # Full state: versions, sessions, golden exemplars
│   └── exports/          # Generated system prompts
│       ├── full.md
│       ├── compact.md
│       └── oneliner.txt
├── another-persona/
│   ├── state.json
│   └── exports/
└── ...
```

### State File Schema

```json
{
  "persona_id": "string",
  "current_version": "integer",
  "tags": {
    "best": "integer (version number)",
    "latest_stable": "integer"
  },

  "versions": [
    {
      "version": 1,
      "persona": { "...full persona object..." },
      "created_at": "ISO 8601",
      "source": "seed | calibration | overhaul | manual",
      "notes": "string (optional, human-provided or auto-generated)"
    }
  ],

  "sessions": [
    {
      "session_id": "string (uuid)",
      "started_at": "ISO 8601",
      "completed_at": "ISO 8601 | null",
      "starting_version": "integer",
      "ending_version": "integer",
      "rounds": [
        {
          "round_number": "integer",
          "questions": [
            {
              "id": "string",
              "text": "string",
              "focus_area": "string",
              "human_answer": "string",
              "persona_answer": "string",
              "scores": {
                "content": "float (1-10)",
                "tone": "float (1-10)",
                "priorities": "float (1-10)",
                "specificity": "float (1-10)",
                "overall": "float (1-10)"
              }
            }
          ],
          "overall_score": "float",
          "changes_proposed": [
            {
              "trait": "string",
              "from": "string",
              "to": "string",
              "confidence": "high | medium | low",
              "rationale": "string",
              "accepted": "boolean"
            }
          ],
          "version_before": "integer",
          "version_after": "integer"
        }
      ]
    }
  ],

  "golden_exemplars": [
    {
      "question": "string",
      "human_answer": "string",
      "persona_answer": "string",
      "overall_score": "float",
      "selected_at_version": "integer"
    }
  ],

  "trait_change_log": [
    {
      "version": "integer",
      "trait": "string",
      "from": "string",
      "to": "string",
      "direction": "string (e.g. 'more casual', 'added new')",
      "impact_score": "float | null (measured after next round)"
    }
  ]
}
```

### Versioning Rules

1. **Every persona mutation creates a new version.** No in-place edits. The `current_version` pointer advances.

2. **Rollback is a pointer change.** `revert_to_version(n)` sets `current_version = n`. All versions are preserved permanently.

3. **Version tagging.** Users can tag versions with labels (`best`, `pre_overhaul`, etc.). Tags are mutable -- you can move the `best` tag to a different version.

4. **Source tracking.** Every version records how it was created (`seed`, `calibration`, `overhaul`, `manual`) for audit trail.

5. **Golden exemplar management.** After each calibration round, if a Q&A pair scores above 8.5 overall, it's automatically added to `golden_exemplars`. The list is capped at 5 entries, keeping the highest-scoring ones. These are used in the export as few-shot examples.

### Trait Change Log

The `trait_change_log` is a flat append-only log of every trait modification. It serves two purposes:

1. **Oscillation detection:** If a trait appears twice in the log with opposite directions within 3 versions, flag it as potentially context-dependent.

2. **Impact tracking:** After each calibration round, the system retrospectively scores how much the previous round's changes affected answer quality. High-impact trait categories get priority in future mutation proposals.

## Data Integrity

- State file is written atomically (write to temp file, then rename)
- Before each write, the previous state file is copied to `state.json.bak`
- All timestamps are UTC ISO 8601
- All IDs are UUIDs (generated via `uuid.uuid4()`)
- Persona IDs are slugified from the name (lowercase, hyphens, no special chars)
