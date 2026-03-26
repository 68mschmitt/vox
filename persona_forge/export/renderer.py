"""System prompt rendering / export.

Takes a calibrated persona and renders it as a deployable system prompt.
POC scope: full format only, print to stdout.

The full export is a deterministic template -- no LLM call needed.

Schema reference: design/PROMPTS.md (Phase 3: Export), design/INTEGRATION.md
"""

from __future__ import annotations

from persona_forge.persona.model import GoldenExemplar, Persona


def render_full(
    persona: Persona,
    exemplars: list[GoldenExemplar] | None = None,
) -> str:
    """Render persona as a full system prompt (1200-2000 tokens).

    Deterministic template -- no LLM call needed.
    For use with Claude Code (CLAUDE.md), ChatGPT custom instructions,
    or direct API usage.

    Args:
        persona: The persona to render.
        exemplars: Optional golden exemplar Q&A pairs for few-shot examples.

    Returns:
        The rendered system prompt as a string.
    """
    sections: list[str] = []

    # Opening identity
    identity_parts = [
        f"You are {persona.name}, a {persona.role}",
    ]
    if persona.identity.years_experience:
        identity_parts[0] += (
            f" with {persona.identity.years_experience} years of experience."
        )
    else:
        identity_parts[0] += "."

    if persona.identity.background:
        identity_parts.append(persona.identity.background)

    sections.append(" ".join(identity_parts))

    # Values
    if persona.values:
        values_lines = ["## Your Values (ranked)"]
        for v in persona.values:
            values_lines.append(f"- {v}")
        sections.append("\n".join(values_lines))

    # Communication style
    comm_parts = ["## How You Communicate"]
    style_parts = []
    if persona.traits.communication_tone.value:
        style_parts.append(f"{persona.traits.communication_tone.value}.")
    if persona.traits.humor.value and persona.traits.humor.value.lower() != "none":
        style_parts.append(f"{persona.traits.humor.value}.")
    if persona.response_patterns.structure:
        style_parts.append(f"{persona.response_patterns.structure}.")
    if persona.response_patterns.length_preference:
        style_parts.append(f"{persona.response_patterns.length_preference}.")
    comm_parts.append(" ".join(style_parts))
    sections.append("\n".join(comm_parts))

    # Decision making
    if persona.decision_heuristics:
        heuristics_lines = ["## How You Make Decisions"]
        for h in persona.decision_heuristics:
            heuristics_lines.append(f"- {h}")
        sections.append("\n".join(heuristics_lines))

    # Technical philosophy
    tech_parts = ["## Your Technical Philosophy"]
    tech_lines = []
    if persona.traits.tool_philosophy.value:
        tech_lines.append(f"{persona.traits.tool_philosophy.value}.")
    if persona.tech_preferences.philosophy:
        tech_lines.append(f"{persona.tech_preferences.philosophy}.")

    pref_parts = []
    if persona.tech_preferences.languages:
        pref_parts.append(f"Languages: {', '.join(persona.tech_preferences.languages)}")
    if persona.tech_preferences.frameworks:
        pref_parts.append(
            f"Frameworks: {', '.join(persona.tech_preferences.frameworks)}"
        )
    if persona.tech_preferences.tools:
        pref_parts.append(f"Tools: {', '.join(persona.tech_preferences.tools)}")
    if pref_parts:
        tech_lines.append("Preferred stack: " + "; ".join(pref_parts) + ".")

    if tech_lines:
        tech_parts.append(" ".join(tech_lines))
        sections.append("\n".join(tech_parts))

    # Personality
    if persona.personality_quirks:
        quirks_lines = ["## Your Personality"]
        for q in persona.personality_quirks:
            quirks_lines.append(f"- {q}")
        sections.append("\n".join(quirks_lines))

    # Frustrations
    if persona.frustrations:
        frust_lines = ["## What Frustrates You"]
        for f in persona.frustrations:
            frust_lines.append(f"- {f}")
        sections.append("\n".join(frust_lines))

    # Anti-patterns
    if persona.anti_patterns:
        anti_lines = ["## What You Never Do"]
        for ap in persona.anti_patterns:
            anti_lines.append(f"- {ap}")
        sections.append("\n".join(anti_lines))

    # Golden exemplars
    if exemplars:
        exemplar_lines = ["## Examples of Your Voice"]
        for e in exemplars[:3]:
            exemplar_lines.append(f"**Q:** {e.question}")
            exemplar_lines.append(f"**A:** {e.human_answer}")
            exemplar_lines.append("")
        sections.append("\n".join(exemplar_lines))

    # Closing instruction
    sections.append(
        f"## Important\n"
        f"Answer all questions as {persona.name}. Let your biases and "
        f"preferences show. Be direct and opinionated. If you'd push back "
        f"on something, push back. You are not a generic AI assistant -- "
        f"you are a specific person with specific views."
    )

    return "\n\n".join(sections)
