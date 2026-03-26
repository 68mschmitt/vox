"""First-draft persona generation from seed input.

Takes SeedData (interview answers + Q&A pairs) and generates
a Persona via LLM.

POC scope: single LLM call to generate persona from seed.

Schema reference: design/PROMPTS.md
"""

from __future__ import annotations

import json

from persona_forge.llm.parse import extract_json, generate_with_retry
from persona_forge.llm.provider import LLMProvider
from persona_forge.persona.model import (
    Identity,
    Persona,
    ResponsePatterns,
    SeedData,
    TechPreferences,
    Trait,
    Traits,
    slugify,
)
from persona_forge.prompts.templates import (
    generate_persona_from_seed as persona_from_seed_prompt,
    get_persona_schema_template,
)
from persona_forge.seed.interview import format_interview_answers, format_qa_pairs
from persona_forge.ui.display import dim


def _parse_persona_from_llm(data: dict, seed: SeedData) -> Persona:
    """Parse LLM-generated JSON into a Persona object.

    Handles missing/malformed fields gracefully by using defaults.
    """
    # Extract traits with fallback
    traits_data = data.get("traits", {})

    def _parse_trait(key: str, default_spectrum: tuple[str, str]) -> Trait:
        t = traits_data.get(key, {})
        if isinstance(t, dict):
            return Trait(
                value=t.get("value", ""),
                spectrum=tuple(t.get("spectrum", list(default_spectrum))),
                calibrated=False,
            )
        # If the LLM returned a string instead of an object
        return Trait(value=str(t), spectrum=default_spectrum, calibrated=False)

    traits = Traits(
        communication_tone=_parse_trait("communication_tone", ("formal", "casual")),
        technical_depth=_parse_trait("technical_depth", ("high-level", "deep-dive")),
        risk_tolerance=_parse_trait("risk_tolerance", ("conservative", "experimental")),
        conflict_style=_parse_trait("conflict_style", ("diplomatic", "blunt")),
        decision_making=_parse_trait("decision_making", ("data-driven", "intuition")),
        humor=_parse_trait("humor", ("none", "frequent")),
        teaching_approach=_parse_trait(
            "teaching_approach", ("socratic", "prescriptive")
        ),
        tool_philosophy=_parse_trait("tool_philosophy", ("proven", "cutting-edge")),
    )

    # Extract identity
    identity_data = data.get("identity", {})
    identity = Identity(
        background=identity_data.get("background", ""),
        daily_workflow=identity_data.get("daily_workflow", ""),
        years_experience=identity_data.get("years_experience", seed.years_experience),
    )

    # Extract response patterns
    rp_data = data.get("response_patterns", {})
    response_patterns = ResponsePatterns(
        structure=rp_data.get("structure", "Direct answer first, then reasoning"),
        length_preference=rp_data.get(
            "length_preference", "Concise unless asked for detail"
        ),
        code_vs_prose=rp_data.get("code_vs_prose", "Balanced"),
    )

    # Extract tech preferences
    tp_data = data.get("tech_preferences", {})
    tech_preferences = TechPreferences(
        languages=tp_data.get("languages", []),
        frameworks=tp_data.get("frameworks", []),
        tools=tp_data.get("tools", []),
        philosophy=tp_data.get("philosophy", ""),
    )

    persona_id = slugify(seed.name)

    return Persona(
        id=persona_id,
        name=seed.name,
        role=seed.role,
        version=1,
        identity=identity,
        traits=traits,
        values=data.get("values", []),
        frustrations=data.get("frustrations", []),
        biases=data.get("biases", []),
        personality_quirks=data.get("personality_quirks", []),
        response_patterns=response_patterns,
        decision_heuristics=data.get("decision_heuristics", []),
        tech_preferences=tech_preferences,
        anti_patterns=data.get("anti_patterns", []),
    )


def generate_persona_from_seed(
    seed_data: SeedData,
    provider: LLMProvider,
) -> Persona:
    """Generate a first-draft persona from seed interview data.

    Calls the LLM with the formatted seed data and persona schema template,
    then parses the response into a Persona object.

    Args:
        seed_data: Collected interview and Q&A data.
        provider: LLM provider for generation.

    Returns:
        A v1 Persona object.
    """
    formatted_answers = format_interview_answers(seed_data.interview_answers)
    formatted_qa = format_qa_pairs(seed_data.qa_pairs)
    schema_template = get_persona_schema_template()

    system_prompt, user_prompt = persona_from_seed_prompt(
        name=seed_data.name,
        role=seed_data.role,
        formatted_interview_answers=formatted_answers,
        formatted_qa_pairs=formatted_qa,
        persona_schema_template=schema_template,
    )

    dim("Generating persona...")
    raw_response = generate_with_retry(
        provider, system_prompt, user_prompt, temperature=0.7
    )
    data = extract_json(raw_response)

    return _parse_persona_from_llm(data, seed_data)
