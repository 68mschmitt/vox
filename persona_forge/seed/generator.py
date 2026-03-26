"""First-draft persona generation from seed input.

Takes SeedData (interview answers + Q&A pairs) and generates
a Persona via LLM.

POC scope: single LLM call to generate persona from seed.

Schema reference: design/PROMPTS.md
"""

from __future__ import annotations

from persona_forge.llm.provider import LLMProvider
from persona_forge.persona.model import Persona, SeedData


def generate_persona_from_seed(
    seed_data: SeedData,
    provider: LLMProvider,
) -> Persona:
    """Generate a first-draft persona from seed interview data.

    Stub — will be implemented in Phase 1 (POC).
    """
    raise NotImplementedError("Persona generation not yet implemented (Phase 1)")
