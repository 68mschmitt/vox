"""Smoke tests — verify the package imports and basic structure."""

from __future__ import annotations


def test_package_imports():
    """Verify the top-level package can be imported."""
    import persona_forge

    assert hasattr(persona_forge, "__version__")
    assert persona_forge.__version__ == "0.1.0"


def test_config_imports():
    """Verify config constants are accessible."""
    from persona_forge.config import (
        CONTENT_WEIGHT,
        CONVERGENCE_SCORE,
        CORE_TRAITS,
        DEFAULT_PROVIDER,
        MAX_ROUNDS_PER_SESSION,
        QUESTIONS_PER_ROUND,
        TONE_WEIGHT,
    )

    assert CONTENT_WEIGHT == 0.30
    assert TONE_WEIGHT == 0.30
    assert CONVERGENCE_SCORE == 8.0
    assert MAX_ROUNDS_PER_SESSION == 4
    assert QUESTIONS_PER_ROUND == 6
    assert DEFAULT_PROVIDER == ""  # empty = auto-detect fallback chain
    assert len(CORE_TRAITS) == 8


def test_model_imports():
    """Verify all data model classes are importable."""
    from persona_forge.persona.model import (
        CalibrationQuestion,
        GoldenExemplar,
        Identity,
        InterviewAnswer,
        Persona,
        QuestionScore,
        ResponsePatterns,
        SeedData,
        SeedQAPair,
        TechPreferences,
        Trait,
        TraitChange,
        Traits,
    )


def test_provider_protocol_importable():
    """Verify the LLM provider protocol is importable."""
    from persona_forge.llm.provider import LLMProvider

    assert LLMProvider is not None


def test_submodules_importable():
    """Verify all submodule stubs are importable."""
    from persona_forge.seed import interview, generator
    from persona_forge.calibrate import loop, questions, evaluator
    from persona_forge.export import renderer
    from persona_forge.prompts import templates
    from persona_forge.ui import display
