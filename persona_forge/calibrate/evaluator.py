"""Divergence analysis and scoring.

POC scope: LLM-based 4-dimension scoring + divergence report.
Alpha: human quick-rating, score reconciliation.

Schema reference: design/EVALUATION.md, design/PROMPTS.md
"""

from __future__ import annotations

from persona_forge.llm.provider import LLMProvider
from persona_forge.persona.model import QuestionScore


def evaluate_answer(
    question_text: str,
    human_answer: str,
    persona_answer: str,
    provider: LLMProvider,
) -> QuestionScore:
    """Score a persona answer against the human's answer.

    Uses the LLM-based 4-dimension evaluation.
    Stub — will be implemented in Phase 1 (POC).
    """
    raise NotImplementedError("Evaluation not yet implemented (Phase 1)")
