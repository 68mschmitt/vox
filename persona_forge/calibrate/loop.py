"""Calibration loop orchestration.

POC scope: single-round calibration only.
Alpha: multi-round with convergence and stall detection.

Schema reference: design/CALIBRATION-LOOP.md
"""

from __future__ import annotations

from persona_forge.llm.provider import LLMProvider
from persona_forge.persona.model import Persona


def run_calibration(
    persona: Persona,
    provider: LLMProvider,
    max_rounds: int = 1,
) -> Persona:
    """Run the calibration loop on a persona.

    POC: single round only.
    Stub — will be implemented in Phase 1 (POC).
    """
    raise NotImplementedError("Calibration loop not yet implemented (Phase 1)")
