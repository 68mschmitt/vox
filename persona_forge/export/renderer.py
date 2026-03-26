"""System prompt rendering / export.

Takes a calibrated persona and renders it as a deployable system prompt.
POC scope: full format only, print to stdout.

The full export is a deterministic template — no LLM call needed.

Schema reference: design/PROMPTS.md (Phase 3: Export)
"""

from __future__ import annotations

from persona_forge.persona.model import GoldenExemplar, Persona


def render_full(
    persona: Persona,
    exemplars: list[GoldenExemplar] | None = None,
) -> str:
    """Render persona as a full system prompt.

    Stub — will be implemented in Phase 1 (POC).
    """
    raise NotImplementedError("Export rendering not yet implemented (Phase 1)")
