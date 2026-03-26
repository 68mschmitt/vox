"""Tests for the seed phase -- interview formatting and generator parsing."""

from __future__ import annotations

import json

from persona_forge.persona.model import (
    InterviewAnswer,
    Persona,
    SeedData,
    SeedQAPair,
)
from persona_forge.seed.generator import _parse_persona_from_llm
from persona_forge.seed.interview import (
    INTERVIEW_QUESTIONS,
    format_interview_answers,
    format_qa_pairs,
)


class TestInterviewQuestions:
    def test_has_8_questions(self):
        """Interview should have exactly 8 questions."""
        assert len(INTERVIEW_QUESTIONS) == 8

    def test_mix_of_types(self):
        """Interview has both choice and freetext questions."""
        types = [q["type"] for q in INTERVIEW_QUESTIONS]
        assert "choice" in types
        assert "freetext" in types

    def test_choices_have_options(self):
        """Choice questions have options lists."""
        for q in INTERVIEW_QUESTIONS:
            if q["type"] == "choice":
                assert "options" in q
                assert len(q["options"]) >= 2


class TestFormatInterviewAnswers:
    def test_format(self):
        """Answers are formatted as Q1/A1, Q2/A2 etc."""
        answers = [
            InterviewAnswer(question="What?", answer="This"),
            InterviewAnswer(question="How?", answer="That"),
        ]
        result = format_interview_answers(answers)
        assert "Q1: What?" in result
        assert "A1: This" in result
        assert "Q2: How?" in result
        assert "A2: That" in result


class TestFormatQAPairs:
    def test_format(self):
        """Q&A pairs are formatted as Q/A blocks."""
        pairs = [
            SeedQAPair(question="Scenario?", answer="My response"),
        ]
        result = format_qa_pairs(pairs)
        assert "Q: Scenario?" in result
        assert "A: My response" in result


class TestParsePersonaFromLlm:
    def _make_seed(self) -> SeedData:
        return SeedData(
            name="Test User",
            role="Engineer",
            years_experience=10,
        )

    def test_full_response(self):
        """Full LLM response parses into a Persona."""
        data = {
            "id": "test-user",
            "name": "Test User",
            "role": "Engineer",
            "identity": {
                "background": "Backend developer",
                "daily_workflow": "Code and review",
                "years_experience": 10,
            },
            "traits": {
                "communication_tone": {
                    "value": "direct",
                    "spectrum": ["formal", "casual"],
                    "calibrated": False,
                },
                "technical_depth": {
                    "value": "deep-dive",
                    "spectrum": ["high-level", "deep-dive"],
                    "calibrated": False,
                },
                "risk_tolerance": {
                    "value": "moderate",
                    "spectrum": ["conservative", "experimental"],
                    "calibrated": False,
                },
                "conflict_style": {
                    "value": "blunt",
                    "spectrum": ["diplomatic", "blunt"],
                    "calibrated": False,
                },
                "decision_making": {
                    "value": "pragmatic",
                    "spectrum": ["data-driven", "intuition"],
                    "calibrated": False,
                },
                "humor": {
                    "value": "dry",
                    "spectrum": ["none", "frequent"],
                    "calibrated": False,
                },
                "teaching_approach": {
                    "value": "socratic",
                    "spectrum": ["socratic", "prescriptive"],
                    "calibrated": False,
                },
                "tool_philosophy": {
                    "value": "proven",
                    "spectrum": ["proven", "cutting-edge"],
                    "calibrated": False,
                },
            },
            "values": ["Simplicity", "Reliability"],
            "frustrations": ["Over-engineering"],
            "biases": ["Skeptical of hype"],
            "personality_quirks": ["Always asks why"],
            "response_patterns": {
                "structure": "Direct first",
                "length_preference": "Concise",
                "code_vs_prose": "Code",
            },
            "decision_heuristics": ["Pick the simpler option"],
            "tech_preferences": {
                "languages": ["Python"],
                "frameworks": [],
                "tools": ["vim"],
                "philosophy": "Simple tools",
            },
            "anti_patterns": ["Never over-engineer"],
        }
        seed = self._make_seed()
        persona = _parse_persona_from_llm(data, seed)

        assert persona.id == "test-user"
        assert persona.name == "Test User"
        assert persona.traits.communication_tone.value == "direct"
        assert persona.values == ["Simplicity", "Reliability"]
        assert persona.version == 1

    def test_missing_fields_use_defaults(self):
        """Missing fields in LLM response use sensible defaults."""
        data = {
            "traits": {
                "communication_tone": {
                    "value": "casual",
                    "spectrum": ["formal", "casual"],
                },
            },
        }
        seed = self._make_seed()
        persona = _parse_persona_from_llm(data, seed)

        assert persona.id == "test-user"
        assert persona.name == "Test User"
        assert persona.traits.communication_tone.value == "casual"
        # Missing traits should have empty value
        assert persona.traits.humor.value in ("none", "")
        assert persona.values == []
        assert persona.frustrations == []

    def test_string_trait_value_handled(self):
        """If LLM returns a string instead of object for a trait, handle gracefully."""
        data = {
            "traits": {
                "communication_tone": "very direct",
            },
        }
        seed = self._make_seed()
        persona = _parse_persona_from_llm(data, seed)
        assert persona.traits.communication_tone.value == "very direct"
