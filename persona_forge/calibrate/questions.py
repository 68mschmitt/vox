"""Calibration question generation.

POC scope: broad coverage question generation (no adaptive).
Alpha: adaptive focus, adversarial questions.

Schema reference: design/CALIBRATION-LOOP.md, design/PROMPTS.md
"""

from __future__ import annotations

from persona_forge.llm.provider import LLMProvider
from persona_forge.persona.model import CalibrationQuestion, Persona


def generate_questions(
    persona: Persona,
    provider: LLMProvider,
    round_number: int = 1,
    count: int = 6,
) -> list[CalibrationQuestion]:
    """Generate calibration questions for a round.

    Stub — will be implemented in Phase 1 (POC).
    """
    raise NotImplementedError("Question generation not yet implemented (Phase 1)")
