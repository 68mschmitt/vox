"""Tests for the persona data model — serialization round-trips."""

from __future__ import annotations

import json

from persona_forge.persona.model import (
    Identity,
    Persona,
    QuestionScore,
    ResponsePatterns,
    TechPreferences,
    Trait,
    Traits,
    slugify,
)


class TestSlugify:
    def test_basic_name(self):
        assert slugify("Eitan Katz") == "eitan-katz"

    def test_special_chars(self):
        assert slugify("John O'Brien") == "john-obrien"

    def test_extra_spaces(self):
        assert slugify("  Multiple   Spaces  ") == "multiple-spaces"

    def test_underscores(self):
        assert slugify("some_name_here") == "some-name-here"


class TestTrait:
    def test_round_trip(self):
        t = Trait("direct and conversational", ("formal", "casual"), True)
        d = t.to_dict()
        t2 = Trait.from_dict(d)
        assert t2.value == t.value
        assert t2.spectrum == t.spectrum
        assert t2.calibrated == t.calibrated

    def test_default_calibrated(self):
        t = Trait.from_dict({"value": "test", "spectrum": ["a", "b"]})
        assert t.calibrated is False


class TestIdentity:
    def test_round_trip(self):
        i = Identity("Backend dev", "Code and review", 10)
        d = i.to_dict()
        i2 = Identity.from_dict(d)
        assert i2.background == i.background
        assert i2.years_experience == i.years_experience


class TestResponsePatterns:
    def test_round_trip(self):
        rp = ResponsePatterns("Direct first", "Concise", "Code over prose")
        d = rp.to_dict()
        rp2 = ResponsePatterns.from_dict(d)
        assert rp2.structure == rp.structure
        assert rp2.code_vs_prose == rp.code_vs_prose


class TestTechPreferences:
    def test_round_trip(self):
        tp = TechPreferences(
            languages=["Python"],
            frameworks=["FastAPI"],
            tools=["neovim"],
            philosophy="Unix tools",
        )
        d = tp.to_dict()
        tp2 = TechPreferences.from_dict(d)
        assert tp2.languages == tp.languages
        assert tp2.philosophy == tp.philosophy

    def test_defaults(self):
        tp = TechPreferences.from_dict({})
        assert tp.languages == []
        assert tp.philosophy == ""


class TestPersona:
    def test_create(self):
        p = Persona.create("Eitan Katz", "Senior Software Engineer")
        assert p.id == "eitan-katz"
        assert p.name == "Eitan Katz"
        assert p.version == 1
        assert p.created_at  # not empty

    def test_round_trip(self, sample_persona: Persona):
        """Full serialize/deserialize round-trip."""
        d = sample_persona.to_dict()
        # Verify it's JSON-serializable
        json_str = json.dumps(d)
        d2 = json.loads(json_str)
        p2 = Persona.from_dict(d2)

        assert p2.id == sample_persona.id
        assert p2.name == sample_persona.name
        assert p2.role == sample_persona.role
        assert p2.version == sample_persona.version
        assert p2.identity.years_experience == sample_persona.identity.years_experience
        assert (
            p2.traits.communication_tone.value
            == sample_persona.traits.communication_tone.value
        )
        assert p2.values == sample_persona.values
        assert p2.frustrations == sample_persona.frustrations
        assert p2.decision_heuristics == sample_persona.decision_heuristics
        assert p2.anti_patterns == sample_persona.anti_patterns
        assert (
            p2.tech_preferences.languages == sample_persona.tech_preferences.languages
        )

    def test_round_trip_minimal(self):
        """Minimal persona (no optional fields) round-trips cleanly."""
        p = Persona.create("Test User", "Developer")
        d = p.to_dict()
        p2 = Persona.from_dict(d)
        assert p2.id == "test-user"
        assert p2.decision_heuristics == []
        assert p2.anti_patterns == []
        assert p2.tech_preferences.languages == []


class TestTraits:
    def test_get_set(self, sample_persona: Persona):
        t = sample_persona.traits.get("humor")
        assert t is not None
        assert "dry" in t.value

    def test_names(self, sample_persona: Persona):
        names = sample_persona.traits.names()
        assert "communication_tone" in names
        assert "humor" in names
        assert len(names) == 8


class TestQuestionScore:
    def test_overall_weighted(self):
        qs = QuestionScore(content=8.0, tone=6.0, priorities=7.0, specificity=5.0)
        # 8*0.30 + 6*0.30 + 7*0.25 + 5*0.15 = 2.4 + 1.8 + 1.75 + 0.75 = 6.7
        assert abs(qs.overall - 6.7) < 0.01

    def test_round_trip(self):
        qs = QuestionScore(content=7.0, tone=5.0, priorities=6.0, specificity=8.0)
        d = qs.to_dict()
        qs2 = QuestionScore.from_dict(d)
        assert qs2.content == qs.content
        assert qs2.tone == qs.tone
        assert abs(qs2.overall - qs.overall) < 0.01
