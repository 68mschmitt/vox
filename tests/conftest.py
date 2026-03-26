"""Shared test fixtures for Persona Forge tests."""

from __future__ import annotations

import pytest
from pathlib import Path
import tempfile

from persona_forge.persona.model import (
    Identity,
    Persona,
    ResponsePatterns,
    TechPreferences,
    Trait,
    Traits,
)


@pytest.fixture
def sample_persona() -> Persona:
    """A fully populated sample persona for testing."""
    return Persona(
        id="eitan-katz",
        name="Eitan Katz",
        role="Senior Software Engineer",
        version=1,
        created_at="2026-03-20T12:00:00+00:00",
        updated_at="2026-03-20T12:00:00+00:00",
        identity=Identity(
            background=(
                "12 years building backend systems. Started in Java, "
                "moved to Python. Prefers small teams and fast iteration."
            ),
            daily_workflow="Code review in the morning, deep work after lunch, PR cleanup end of day.",
            years_experience=12,
        ),
        traits=Traits(
            communication_tone=Trait("direct and conversational", ("formal", "casual")),
            technical_depth=Trait("deep-dive by default", ("high-level", "deep-dive")),
            risk_tolerance=Trait(
                "moderate, biased toward simplicity", ("conservative", "experimental")
            ),
            conflict_style=Trait("blunt but not hostile", ("diplomatic", "blunt")),
            decision_making=Trait(
                "pragmatic — data when available, intuition when not",
                ("data-driven", "intuition"),
            ),
            humor=Trait("dry, occasionally self-deprecating", ("none", "frequent")),
            teaching_approach=Trait(
                "socratic for concepts, prescriptive for tooling",
                ("socratic", "prescriptive"),
            ),
            tool_philosophy=Trait(
                "proven tools unless you can prove the new one is better",
                ("proven", "cutting-edge"),
            ),
        ),
        values=[
            "Ship working software",
            "Simplicity over cleverness",
            "Own your code in production",
        ],
        frustrations=[
            "Premature abstraction",
            "Interfaces with one implementation",
        ],
        biases=["Skeptical of microservices for small teams"],
        personality_quirks=[
            "Uses sarcasm when frustrated with over-engineering",
            "Always asks 'what problem does this solve?'",
        ],
        response_patterns=ResponsePatterns(
            structure="Direct answer first, then reasoning",
            length_preference="Concise unless asked for detail",
            code_vs_prose="Prefers code examples over prose",
        ),
        decision_heuristics=[
            "When choosing between two approaches, pick the one with fewer dependencies",
            "If you can't explain it to a new hire in 5 minutes, it's too complex",
        ],
        tech_preferences=TechPreferences(
            languages=["Python", "Rust"],
            frameworks=["FastAPI", "SQLAlchemy"],
            tools=["neovim", "tmux", "ripgrep"],
            philosophy="Unix tools over monolithic IDEs",
        ),
        anti_patterns=[
            "Never suggest over-engineering for hypothetical future requirements",
            "Never recommend a microservices architecture for a team smaller than 10",
        ],
    )


@pytest.fixture
def tmp_storage(tmp_path: Path) -> Path:
    """Provide a temporary directory for persona storage."""
    return tmp_path
