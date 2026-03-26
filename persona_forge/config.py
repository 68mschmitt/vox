"""Configuration constants for Persona Forge.

All calibration parameters, scoring weights, and loop control constants
are defined here. Values are sourced from the design docs:
- CALIBRATION-LOOP.md
- EVALUATION.md
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
DEFAULT_PERSONAS_DIR = Path("personas")
PERSONAS_DIR = Path(os.environ.get("PERSONA_FORGE_DIR", str(DEFAULT_PERSONAS_DIR)))

# ---------------------------------------------------------------------------
# LLM Provider
# ---------------------------------------------------------------------------
# When PERSONA_FORGE_PROVIDER is set, it acts as an explicit choice (no
# fallback).  When unset, the factory auto-detects: bedrock -> ollama ->
# anthropic.  See persona_forge.llm.create_provider().
DEFAULT_PROVIDER = os.environ.get("PERSONA_FORGE_PROVIDER", "")
DEFAULT_MODEL = os.environ.get("PERSONA_FORGE_MODEL", "claude-sonnet-4-20250514")
DEFAULT_TEMPERATURE = 0.7

# Environment variable names for API keys
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OLLAMA_HOST_ENV = "OLLAMA_HOST"
OLLAMA_DEFAULT_HOST = "http://localhost:11434"

# Amazon Bedrock
AWS_BEARER_TOKEN_BEDROCK_ENV = "AWS_BEARER_TOKEN_BEDROCK"
AWS_BEDROCK_REGION_ENV = "AWS_BEDROCK_REGION"
BEDROCK_DEFAULT_REGION = "us-east-1"
BEDROCK_DEFAULT_MODEL = "us.anthropic.claude-sonnet-4-20250514-v1:0"

# ---------------------------------------------------------------------------
# Scoring Weights (EVALUATION.md)
# ---------------------------------------------------------------------------
CONTENT_WEIGHT = 0.30
TONE_WEIGHT = 0.30
PRIORITIES_WEIGHT = 0.25
SPECIFICITY_WEIGHT = 0.15

# ---------------------------------------------------------------------------
# Human Rating Adjustments (EVALUATION.md)
# ---------------------------------------------------------------------------
NAILED_IT_FLOOR = 7  # Minimum score when human says "Nailed it"
CLOSE_BUT_OFF_PENALTY = 1  # Penalty for dimensions mentioned in notes
WAY_OFF_CAP = 5  # Max score when human says "Way off"
WAY_OFF_MENTIONED_CAP = 3  # Max for specifically mentioned dimensions

# ---------------------------------------------------------------------------
# Advanced Evaluation Checks (EVALUATION.md)
# ---------------------------------------------------------------------------
BLIND_TEST_FREQUENCY = 2  # Questions per round for blind comparison
CONSISTENCY_WARNING = 7.0  # Below this triggers coherence flag
REGRESSION_THRESHOLD = 1.5  # Score drop to trigger regression warning

# ---------------------------------------------------------------------------
# Convergence (CALIBRATION-LOOP.md / EVALUATION.md)
# ---------------------------------------------------------------------------
CONVERGENCE_SCORE = 8.0  # Overall score target
CONVERGENCE_ROUNDS = 2  # Consecutive rounds above threshold

# ---------------------------------------------------------------------------
# Calibration Loop Control (CALIBRATION-LOOP.md)
# ---------------------------------------------------------------------------
MAX_ROUNDS_PER_SESSION = 4  # Hard cap on rounds per session
STALL_THRESHOLD = 0.3  # Minimum score improvement to avoid stall
STALL_ROUNDS = 2  # Consecutive stall rounds before overhaul

# ---------------------------------------------------------------------------
# Mutation (CALIBRATION-LOOP.md)
# ---------------------------------------------------------------------------
MAX_TRAIT_CHANGES_PER_ROUND = 4
REGRESSION_REVERT_THRESHOLD = 1.0  # Score drop that triggers auto-revert
OSCILLATION_LOOKBACK = 3  # Versions to check for oscillation

# ---------------------------------------------------------------------------
# Question Generation (CALIBRATION-LOOP.md)
# ---------------------------------------------------------------------------
QUESTIONS_PER_ROUND = 6
REGRESSION_QUESTIONS = 1  # Questions from strong areas per round
ADVERSARIAL_ROUND_START = 3  # Round to start adversarial questions

# ---------------------------------------------------------------------------
# Golden Exemplars (CALIBRATION-LOOP.md)
# ---------------------------------------------------------------------------
GOLDEN_EXEMPLAR_THRESHOLD = 8.5
MAX_GOLDEN_EXEMPLARS = 5

# ---------------------------------------------------------------------------
# Seed Interview
# ---------------------------------------------------------------------------
SEED_INTERVIEW_QUESTION_COUNT = 8
SEED_FOLLOWUP_QUESTION_COUNT = 2

# ---------------------------------------------------------------------------
# Persona Schema
# ---------------------------------------------------------------------------
CORE_TRAITS = [
    "communication_tone",
    "technical_depth",
    "risk_tolerance",
    "conflict_style",
    "decision_making",
    "humor",
    "teaching_approach",
    "tool_philosophy",
]

MAX_TRAIT_COUNT = 15  # Beyond this, trait interactions become unmanageable
