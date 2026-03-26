"""Divergence analysis and scoring.

POC scope: LLM-based 4-dimension scoring + divergence report.
Alpha: human quick-rating, score reconciliation.

Schema reference: design/EVALUATION.md, design/PROMPTS.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from persona_forge.config import (
    CONTENT_WEIGHT,
    TONE_WEIGHT,
    PRIORITIES_WEIGHT,
    SPECIFICITY_WEIGHT,
)
from persona_forge.llm.parse import extract_json, generate_with_retry
from persona_forge.llm.provider import LLMProvider
from persona_forge.persona.model import Persona, QuestionScore
from persona_forge.prompts.templates import (
    evaluate_divergence as evaluate_divergence_prompt,
    generate_persona_answer,
)
from persona_forge.ui.display import dim


def _generate_persona_answer(
    persona: Persona,
    question_text: str,
    provider: LLMProvider,
) -> str:
    """Generate the persona's in-character answer to a question.

    Args:
        persona: The persona to answer as.
        question_text: The question to answer.
        provider: LLM provider.

    Returns:
        The persona's answer text.
    """
    # Format persona as JSON for the prompt
    persona_json = json.dumps(persona.to_dict(), indent=2)

    # Collect golden exemplars if available (empty list for POC)
    golden_exemplars: list[dict[str, str]] = []

    system_prompt, user_prompt = generate_persona_answer(
        name=persona.name,
        role=persona.role,
        formatted_persona_json=persona_json,
        communication_tone=persona.traits.communication_tone.value,
        humor=persona.traits.humor.value,
        decision_making=persona.traits.decision_making.value,
        risk_tolerance=persona.traits.risk_tolerance.value,
        response_structure=persona.response_patterns.structure,
        question_text=question_text,
        golden_exemplars=golden_exemplars,
    )

    return generate_with_retry(provider, system_prompt, user_prompt, temperature=0.7)


def evaluate_answer(
    question_text: str,
    human_answer: str,
    persona_answer: str,
    provider: LLMProvider,
) -> QuestionScore:
    """Score a persona answer against the human's answer.

    Uses the LLM-based 4-dimension evaluation from EVALUATION.md.

    Args:
        question_text: The original question.
        human_answer: The human's reference answer.
        persona_answer: The persona's generated answer.
        provider: LLM provider for evaluation.

    Returns:
        QuestionScore with content, tone, priorities, specificity scores.
    """
    system_prompt, user_prompt = evaluate_divergence_prompt(
        question_text=question_text,
        human_answer=human_answer,
        persona_answer=persona_answer,
    )

    raw_response = generate_with_retry(
        provider, system_prompt, user_prompt, temperature=0.3
    )
    data = extract_json(raw_response)

    # Parse scores from the evaluation response
    def _get_score(dimension: str) -> float:
        dim_data = data.get(dimension, {})
        if isinstance(dim_data, dict):
            score = dim_data.get("score", 5.0)
        elif isinstance(dim_data, (int, float)):
            score = dim_data
        else:
            score = 5.0
        # Clamp to valid range
        return max(1.0, min(10.0, float(score)))

    return QuestionScore(
        content=_get_score("content"),
        tone=_get_score("tone"),
        priorities=_get_score("priorities"),
        specificity=_get_score("specificity"),
    )


@dataclass
class EvaluationResult:
    """Full evaluation result for a single question."""

    question_id: str
    question_text: str
    category: str
    human_answer: str
    persona_answer: str
    scores: QuestionScore

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "category": self.category,
            "human_answer": self.human_answer,
            "persona_answer": self.persona_answer,
            "scores": self.scores.to_dict(),
        }


@dataclass
class DivergenceReport:
    """Aggregate divergence report for a calibration round."""

    results: list[EvaluationResult]

    @property
    def overall_score(self) -> float:
        """Average overall score across all questions."""
        if not self.results:
            return 0.0
        return sum(r.scores.overall for r in self.results) / len(self.results)

    @property
    def dimension_averages(self) -> dict[str, float]:
        """Average score per dimension across all questions."""
        if not self.results:
            return {"content": 0, "tone": 0, "priorities": 0, "specificity": 0}

        n = len(self.results)
        return {
            "content": sum(r.scores.content for r in self.results) / n,
            "tone": sum(r.scores.tone for r in self.results) / n,
            "priorities": sum(r.scores.priorities for r in self.results) / n,
            "specificity": sum(r.scores.specificity for r in self.results) / n,
        }

    @property
    def weakest_dimension(self) -> str:
        """The dimension with the lowest average score."""
        avgs = self.dimension_averages
        return min(avgs, key=avgs.get)  # type: ignore[arg-type]

    @property
    def strongest_dimension(self) -> str:
        """The dimension with the highest average score."""
        avgs = self.dimension_averages
        return max(avgs, key=avgs.get)  # type: ignore[arg-type]

    def format_for_prompt(self) -> str:
        """Format the report for use in the trait change proposal prompt."""
        lines = [
            f"Overall Score: {self.overall_score:.1f} / 10",
            "",
            "Dimension Averages:",
        ]
        for dim_name, avg in self.dimension_averages.items():
            lines.append(f"  {dim_name}: {avg:.1f}")
        lines.append(f"\nWeakest: {self.weakest_dimension}")
        lines.append(f"Strongest: {self.strongest_dimension}")
        lines.append("\nPer-Question Results:")

        for r in self.results:
            qt = (
                r.question_text[:80] + "..."
                if len(r.question_text) > 80
                else r.question_text
            )
            lines.append(f"\n  [{r.category}] {qt}")
            lines.append(
                f"    Content: {r.scores.content:.0f} | "
                f"Tone: {r.scores.tone:.0f} | "
                f"Priorities: {r.scores.priorities:.0f} | "
                f"Specificity: {r.scores.specificity:.0f} | "
                f"Overall: {r.scores.overall:.1f}"
            )
            ha = r.human_answer[:100] + ("..." if len(r.human_answer) > 100 else "")
            pa = r.persona_answer[:100] + ("..." if len(r.persona_answer) > 100 else "")
            lines.append(f"    Human answer: {ha}")
            lines.append(f"    Persona answer: {pa}")

        return "\n".join(lines)


def generate_persona_answer_text(
    persona: Persona,
    question_text: str,
    provider: LLMProvider,
) -> str:
    """Public wrapper for persona answer generation.

    Used by the calibration loop to generate persona answers for each question.
    """
    return _generate_persona_answer(persona, question_text, provider)
