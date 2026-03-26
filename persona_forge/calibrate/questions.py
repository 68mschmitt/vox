"""Calibration question generation.

POC scope: broad coverage question generation (no adaptive).
Alpha: adaptive focus, adversarial questions.

Schema reference: design/CALIBRATION-LOOP.md, design/PROMPTS.md
"""

from __future__ import annotations

from persona_forge.config import QUESTIONS_PER_ROUND
from persona_forge.llm.parse import extract_json, generate_with_retry
from persona_forge.llm.provider import LLMProvider
from persona_forge.persona.model import CalibrationQuestion, Persona
from persona_forge.prompts.templates import generate_calibration_questions
from persona_forge.ui.display import dim


# POC: broad coverage distribution spec for Round 1
BROAD_COVERAGE_SPEC = """Distribute questions across these categories (1 each minimum):
- architecture: System design decisions
- code_review: Code review scenarios
- debugging: Debugging and incident response
- conflict: Team disagreements and interpersonal
- tooling: Tool/framework/language selection
- tradeoff: Trade-off framing and estimation"""


def generate_questions(
    persona: Persona,
    provider: LLMProvider,
    round_number: int = 1,
    count: int | None = None,
) -> list[CalibrationQuestion]:
    """Generate calibration questions for a round.

    POC: Generates broad coverage questions (Round 1 only).

    Args:
        persona: The persona to generate questions for.
        provider: LLM provider.
        round_number: Round number (always 1 for POC).
        count: Number of questions (defaults to QUESTIONS_PER_ROUND).

    Returns:
        List of CalibrationQuestion objects.
    """
    question_count = count or QUESTIONS_PER_ROUND

    # Build tech preferences summary
    tech_summary_parts = []
    if persona.tech_preferences.languages:
        tech_summary_parts.append(
            f"Languages: {', '.join(persona.tech_preferences.languages)}"
        )
    if persona.tech_preferences.tools:
        tech_summary_parts.append(f"Tools: {', '.join(persona.tech_preferences.tools)}")
    if persona.tech_preferences.philosophy:
        tech_summary_parts.append(persona.tech_preferences.philosophy)
    tech_summary = (
        "; ".join(tech_summary_parts) if tech_summary_parts else "Not specified"
    )

    system_prompt, user_prompt = generate_calibration_questions(
        name=persona.name,
        role=persona.role,
        values=persona.values,
        communication_tone=persona.traits.communication_tone.value,
        tech_preferences_summary=tech_summary,
        round_number=round_number,
        question_count=question_count,
        question_distribution_spec=BROAD_COVERAGE_SPEC,
    )

    dim(f"Generating {question_count} calibration questions...")
    raw_response = generate_with_retry(
        provider, system_prompt, user_prompt, temperature=0.7
    )
    data = extract_json(raw_response)

    questions_data = data.get("questions", [])
    questions: list[CalibrationQuestion] = []
    for i, q in enumerate(questions_data[:question_count]):
        questions.append(
            CalibrationQuestion(
                id=q.get("id", f"q{i + 1}"),
                text=q.get("text", ""),
                category=q.get("category", "unknown"),
                focus_area=q.get("focus_area", ""),
                difficulty=q.get("difficulty", "standard"),
            )
        )

    if not questions:
        raise RuntimeError(
            "LLM failed to generate calibration questions. "
            "Check your API key and try again."
        )

    return questions
